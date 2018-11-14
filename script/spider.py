import traceback
import json, re
import time
from weibo import MWeiboCn
from functools import reduce
import urllib.request
import socket
import config
socket.setdefaulttimeout(5)

global count
count = 0
confirm_num = config.get_parser().getint('scan','confirm_num')
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
			weibo_api(db,status['id'],'insert')
		elif 'edit_count' in status:
			_,edit_count = cursor.fetchone()
			if edit_count < status['edit_count']:
				print('{}. [Edited] Updating user: {} weibo_id: {}'.format(count,screen_name,status['id']))
				weibo_api(db,status['id'],'update')

def user_weibo_update(db,uid,min_id):
	cursor = db.cursor()
	
	user_update(db,uid)
	cursor.execute("SELECT id,max_mid FROM weibo_user WHERE id=%s",(uid,))
	_,min_id = cursor.fetchone()
	page = 1
	while scan_page(uid,page,min_id):
		page += 1

	cursor.execute("SELECT id,uid FROM weibo_index WHERE uid=%s ORDER BY id DESC LIMIT 1")
	max_mid,_ = cursor.fetchone()
	try:
		cursor.execute("UPDATE weibo_user SET max_mid=%s WHERE id=%s",(max_mid,uid))
		db.commit()
	except:
		db.rollback()
		raise


def user_update(db,id):
	cursor = db.cursor()

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


def scan_user_all(db,uid,restart=False):
	cursor = db.cursor()
	if not cursor.execute("SELECT scan_page,screen_name FROM weibo_user WHERE id=%s",(uid,)):
		user_update(db,uid)
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
		#获取微博列表
		#global count
		#count += 1
		#if count > 800:
		#	exit()

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

def get_retweeted_status(id):
	data = client.status(id)
	if data is None:
		raise Exception('data error')
	else:
		if 'retweeted_status' in data['status']:
			return data['status']['retweeted_status']
		else:
			return None
	

def weibo_api(db,id,operation='insert'):

	global count
	count += 1

	cursor = db.cursor()
	content = client.status(id,decode=False)
	if content is not None:
		with urllib.request.urlopen('http://localhost/weibo/api/{}_weibo.php'.format(operation),urllib.parse.urlencode({"data":content}).encode("ascii")) as f:
			reponse = f.read().decode()
			result = json.loads(reponse)
			if result['errorCode'] != "0" and result['errorCode'] != "101":
				raise Exception(reponse)

if __name__ == '__main__':
	db = config.get_db_connect()
	users = config.get_scan_users()
	for uid in users:
		scan_user_all(db,uid,restart=False)
		#user_weibo_update(db,uid,min_id="4282634743679613")
	db.close()
