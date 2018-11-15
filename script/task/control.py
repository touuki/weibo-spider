import json, re
import time
from functools import reduce
import urllib.request
import socket
from .workers import app
import MySQLdb
from DBUtils.PooledDB import PooledDB

_pool = PooledDB(creator=MySQLdb, mincached=1, maxcached=20,
 host=Config.DBHOST , port=Config.DBPORT , user=Config.DBUSER , passwd=Config.DBPWD ,
 db=Config.DBNAME,use_unicode=False,charset=Config.DBCHAR)

@app.task
def single_weibo(status):
	db = _pool.connection()
	cursor = db.cursor()
	try:
		if status['user'] is None:
			print('weibo_id: {} no user, maybe deleted.')
		else:
			screen_name = status['user']['screen_name']
			if not cursor.execute("SELECT id,edit_count FROM weibo_index WHERE id=%s",(status['id'],)):
				print('{}. Updating user: {} weibo_id: {}'.format(count,screen_name,status['id']))
				target.weibo_api.delay(status['id'],'insert')
			elif 'edit_count' in status:
				_,edit_count = cursor.fetchone()
				if edit_count < status['edit_count']:
					print('{}. [Edited] Updating user: {} weibo_id: {}'.format(count,screen_name,status['id']))
					target.weibo_api.delay(status['id'],'update')
	finally:
		cursor.close()
		db.close()

@app.task
def update_max_mid(uid):
	db = _pool.connection()
	cursor = db.cursor()
	try:
		if cursor.execute("SELECT id,user_id FROM weibo_index WHERE user_id=%s ORDER BY id DESC LIMIT 1",(uid,)):
			max_mid,_ = cursor.fetchone()
			try:
				cursor.execute("UPDATE weibo_user SET max_mid=%s WHERE id=%s",(max_mid,uid))
				db.commit()
			except:
				db.rollback()
				raise
	finally:
		cursor.close()
		db.close()

@app.task
def user_weibo_update(uid):
	db = _pool.connection()
	cursor = db.cursor()
	try:
		target.user_update.delay(uid)
		cursor.execute("SELECT id,max_mid FROM weibo_user WHERE id=%s",(uid,))
		_,min_id = cursor.fetchone()
		target.scan_page.delay(uid,1,min_id)
	finally:
		cursor.close()
		db.close()

@app.task
def user_update(res):
	db = _pool.connection()
	cursor = db.cursor()
	try:
		try:
			data = json.loads(res)['data']
		except json.decoder.JSONDecodeError:
			#此情况可能为uid不存在
			print('user id:' + id + ' Error!')
			raise
		insert_data = {'id':data['userInfo']['id'],
		'screen_name':data['userInfo']['screen_name'],
		'follow_count':data['userInfo']['follow_count'],
		'followers_count':data['userInfo']['followers_count'],
		'statuses_count':data['userInfo']['statuses_count'],
		'description':data['userInfo']['description'],
		'original_data':res
		}	
		try:	
			#判断数据库中是否已存在
			if cursor.execute("SELECT id FROM weibo_user WHERE id=%s",(data['userInfo']['id'],)):
				cursor.execute("UPDATE weibo_user SET " + reduce(lambda x,y:x+y,[k + "=%(" + k + ")s," for k in insert_data])[:-1] 
						+ " WHERE id=%(id)s",insert_data)
			else:
				cursor.execute("INSERT INTO weibo_user ( " + reduce(lambda x,y:x+y,[ k + "," for k in insert_data])[:-1] 
						+ " ) VALUES ( " + reduce(lambda x,y:x+y,[ "%(" + k + ")s," for k in insert_data])[:-1] + " )",insert_data)
			db.commit()
		except:
			db.rollback()
			raise
	finally:
		cursor.close()
		db.close()

@app.task
def scan_user_all(uid,restart=False):
	cursor = db.cursor()
	if not cursor.execute("SELECT scan_page,screen_name FROM weibo_user WHERE id=%s",(uid,)):
		return

	#page为已经扫描到的页数
	page,_ = cursor.fetchone()

	if page<0:
		if restart:
			page = 1
		else:
			return
	else:
		page += 1

	while scan_page(uid,page):
		try:
			cursor.execute("UPDATE weibo_user SET scan_page=%s WHERE id=%s",(page,uid))
			db.commit()
		except:
			db.rollback()
			raise
		page += 1

	#扫描完后scan_page设为负
	try:
		cursor.execute("UPDATE weibo_user SET scan_page=%s WHERE id=%s",(-page+1,uid))
		db.commit()
	except:
		db.rollback()
		raise

	update_max_mid(db,uid)