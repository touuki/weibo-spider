import traceback
import json, re
import time
from weibo import MWeiboCn
from functools import reduce
import urllib.request
import socket
import config
import datetime
socket.setdefaulttimeout(5)

global count
count = 0
client = config.get_weibo_client()
if not client.st:
	client.login()

def scan_page(uid,page,min_id = 0, request_count = 1):
	data = client.getIndex_contents(uid,page)
	#已扫描完退出，访问太频繁有几率不返回内容，故多请求几次
	if data['ok'] == 0:
		if request_count < 3:
			request_count += 1
			time.sleep(request_count)
			return scan_page(uid,page,min_id = min_id,request_count = request_count + 1)
		else:
			return False

	data = data['data']
	print("user: %s page: %s" % (uid,page))
	for card in data['cards']:
		if card['card_type']==9:
			id = card['mblog']['id']
			if int(id) < int(min_id) and 'isTop' not in card['mblog']:
				return False

			if 'retweeted_status' in card['mblog']:
				retweeted_status = card['mblog']['retweeted_status']
				#未登录情况下访问频繁会403，较久远微博retweeted_status的id等内容有时会为空
				while not retweeted_status['id']:
					print('retweeted_id is empty, try the other way, weibo_id: ' + id)
					retweeted_status = get_retweeted_status(id)
				single_weibo(retweeted_status)

			single_weibo(card['mblog'])

	return True

def single_weibo(status):
	
	if status['user'] is None:
		print('weibo_id: {} no user, maybe deleted.')
	else:
		screen_name = status['user']['screen_name']
		if not cursor.execute("SELECT id,edit_count FROM weibo_index WHERE id=%s",(status['id'],)):
			print('{}. Updating user: {} weibo_id: {}'.format(count,screen_name,status['id']))
			weibo_api(status['id'],'insert')
		elif 'edit_count' in status:
			_,edit_count = cursor.fetchone()
			if edit_count < status['edit_count']:
				print('{}. [Edited] Updating user: {} weibo_id: {}'.format(count,screen_name,status['id']))
				weibo_api(status['id'],'update')

def user_weibo_update(uid):
	user_update(uid)
	cursor.execute("SELECT id,max_mid FROM weibo_user WHERE id=%s",(uid,))
	_,min_id = cursor.fetchone()
	page = 1
	while scan_page(uid,page,min_id):
		page += 1

	update_max_mid(uid)


def update_max_mid(uid):
	
	if cursor.execute("SELECT id,user_id FROM weibo_index WHERE user_id=%s ORDER BY id DESC LIMIT 1",(uid,)):
		max_mid,_ = cursor.fetchone()
		try:
			cursor.execute("UPDATE weibo_user SET max_mid=%s WHERE id=%s",(max_mid,uid))
			db.commit()
		except:
			db.rollback()
			raise


def user_update(id):
	

	res = client._getIndex_user(id)
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


def scan_user_all(uid,restart=False):
	
	if not cursor.execute("SELECT scan_page,screen_name FROM weibo_user WHERE id=%s",(uid,)):
		user_update(uid)
		cursor.execute("SELECT scan_page,screen_name FROM weibo_user WHERE id=%s",(uid,))

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
		#更新扫描页面
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

	update_max_mid(uid)

def get_retweeted_status(id):
	data = client.status(id)
	if data is None:
		raise Exception('data error')
	else:
		if 'retweeted_status' in data['status']:
			return data['status']['retweeted_status']
		else:
			return None
	

def weibo_api(id,operation='insert'):
	global count
	count += 1
	content = client.status(id,decode=False)
	status = json.loads(content)['status']
	sql_data = {}
	if content is not None:
		try:
			sql_data['edit_count'] = 0 if 'edit_count' not in status else status['edit_count']
			sql_data['edit_at'] = None if 'edit_at' not in status else datetime.datetime.strptime(status['edit_at'], '%a %b %d %H:%M:%S %z %Y')
			sql_data['created_at'] = datetime.datetime.strptime(status['created_at'], '%a %b %d %H:%M:%S %z %Y')
			sql_data['text'] = status['text']
			sql_data['id'] = status['id']
			sql_data['user_screen_name'] = status['user']['screen_name']
			sql_data['user_id'] = status['user']['id']
			sql_data['bid'] = status['bid']
			sql_data['reposts_count'] = status['reposts_count']
			sql_data['comments_count'] = status['comments_count']
			sql_data['attitudes_count'] = status['attitudes_count']
			sql_data['original_data'] = content
			sql_data['pic_ids'] = json.dumps(status['pic_ids'])
			sql_data['page_info'] = None if 'page_info' not in status else json.dumps(status['page_info'], ensure_ascii=False)
			sql_data['retweeted_id'] = None if 'retweeted_status' not in status else status['retweeted_status']['id']

			if operation == 'update':
				cursor.execute('UPDATE weibo_index SET text=%(text)s , user_screen_name=%(user_screen_name)s ,\
				 reposts_count=%(reposts_count)s , comments_count=%(comments_count)s , attitudes_count=%(attitudes_count)s ,\
				  original_data=%(original_data)s , pic_ids=%(pic_ids)s, page_info=%(page_info)s, edit_count=%(edit_count)s, \
				  edit_at=%(edit_at)s WHERE id=%(id)s',sql_data)
			else:
				cursor.execute('INSERT INTO weibo_index (id , created_at , text , user_id , user_screen_name , reposts_count ,\
				 comments_count , attitudes_count , bid , original_data , retweeted_id , pic_ids, page_info, edit_at, edit_count)\
				  VALUES (%(id)s , %(created_at)s , %(text)s , %(user_id)s , %(user_screen_name)s , %(reposts_count)s , \
				  %(comments_count)s , %(attitudes_count)s , %(bid)s , %(original_data)s , %(retweeted_id)s , %(pic_ids)s ,\
				   %(page_info)s, %(edit_at)s, %(edit_count)s)',sql_data)

			if 'pics' in status:
				for pic in status['pics']:
					update_pic(pic,status['id'])
					
			db.commit()
		except:
			db.rollback()
			raise



def update_pic(pic,mid):
	if not cursor.execute('SELECT pid FROM weibo_pic WHERE pid=%s',(pic['pid'],)):
		cursor.execute('INSERT INTO weibo_pic (pid , type , mid) VALUES (%s , %s , %s)',(pic['pid'],pic['url'].split('.')[-1],mid))
		orj360_height = int(pic['geo']['height'])
		if orj360_height > 1200:
			orj360_height = 1200
		cursor.execute('INSERT INTO weibo_pic_orj360 (pid , width , height , croped , url) VALUES (%s , %s , %s , %s , %s)',
			(pic['pid'],pic['geo']['width'],orj360_height,pic['geo']['croped'],pic['url']))
		cursor.execute('INSERT INTO weibo_pic_large (pid , width , height , croped , url) VALUES (%s , %s , %s , %s , %s)',
			(pic['pid'],pic['large']['geo']['width'],pic['large']['geo']['height'],pic['large']['geo']['croped'],pic['large']['url']))

def scan_comments(mid,page,uids=None):
	
	data = client.comments_show(mid,page)
	#已扫描完退出，访问太频繁有几率不返回内容，故多请求几次
	if data['ok'] == 0:
		return False
	try:
		data = data['data']
		print("mid: %s page: %s" % (mid,page))
		for comment in data['data']:
			if not cursor.execute('SELECT id FROM weibo_comment WHERE id=%s',(comment['id'],)) and (uids is None or comment['user']['id'] in uids):
				if 'pic' in comment:
					pic_id = comment['pic']['pid']
					update_pic(comment['pic'],mid)
				else:
					pic_id = None
				cursor.execute('INSERT INTO weibo_comment (id, text, created_at, pic_id, mid,  user_id) VALUES (%s,%s,%s,%s,%s,%s)',
						(comment['id'],comment['text'],comment['created_at'],pic_id,mid,comment['user']['id']))

		db.commit()
		return True
	except:
		db.rollback()
		raise

def scan_all_comments(mid,page,uids=None,restart=False):
	if page<0:
		if restart:
			page = 1
		else:
			return
	else:
		page += 1

	while scan_comments(mid,page,uids):
		try:
			cursor.execute("UPDATE weibo_index SET comments_page=%s WHERE id=%s",(page,mid))
			db.commit()
		except:
			db.rollback()
			raise
		page += 1

	if page == 1:
		page += 1
	try:
		cursor.execute("UPDATE weibo_index SET comments_page=%s WHERE id=%s",(-page+1,mid))
		db.commit()
	except:
		db.rollback()
		raise

if __name__ == '__main__':
	db = config.get_db_connect()
	cursor = db.cursor()
	users = config.get_scan_users()
	for uid in users:
		#scan_user_all(uid,restart=False)
		user_weibo_update(uid)
		#cursor.execute("SELECT id,comments_page FROM weibo_index WHERE user_id=%s",(uid,))
		#for mid,page in cursor.fetchall():
		#	scan_all_comments(mid,page,[int(uid)])
	db.close()
