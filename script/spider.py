import traceback
import json, re
import time
from weibo import MWeiboCn
from functools import reduce
import urllib.request
import socket
import util
socket.setdefaulttimeout(5)

global COUNT
COUNT = 0

client = util.getWeiboClient()
if not client.st:
	client.login()

def user_weibo_update(db,uid,min_id=None):
	cursor = db.cursor()
	
	user_update(db,uid)
	cursor.execute("SELECT id,screen_name FROM weibo_user WHERE id=%s",(uid,))
	users = cursor.fetchall()
	
	'''
	cursor.execute("SELECT id FROM weibo_index WHERE user_id=%s ORDER BY id DESC LIMIT 1",(uid,))
	last_id = cursor.fetchall()
	if last_id:
		last_id = last_id[0][0]
	else:
		last_id = 0
	'''

	page = 1
	read_count = 0
	not_ok_count = 0
	idcount = 0
	while True:
		if min_id is None and read_count >= 8:
			break

		data = client.getIndex_list(uid,page)
		#已扫描完退出，访问太频繁有几率不返回内容，故多请求几次
		if data['ok']==0 :
			if not_ok_count<2 :
				not_ok_count += 1
				time.sleep(not_ok_count)
				continue
			else :
				break

		data = data['data']
		print("user: %s page: %s" % (users[0][1],page))
		for card in data['cards']:
			if card['card_type']==9:
				id = card['mblog']['id']
				if min_id and int(id) < int(min_id):
					if idcount>2:
						return
					else:
						idcount += 1

				if 'retweeted_status' in card['mblog']:
					rid = card['mblog']['retweeted_status']['id']
					if not cursor.execute("SELECT id FROM weibo_index WHERE id=%s",(rid,)):
						print(str(COUNT) + '. Updating retweeted_status: ' + users[0][1] + ' weibo_id: ' + id + "  " + rid)
						weibo_insert(db,rid)

				if not cursor.execute("SELECT id FROM weibo_index WHERE id=%s",(id,)):
					print(str(COUNT) + '. Updating user: ' + users[0][1] + ' weibo_id: ' + id)
					weibo_insert(db,id)
				else:
					read_count += 1

		page += 1
		not_ok_count = 0


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
	cursor.execute("SELECT scan_page,screen_name FROM weibo_user WHERE id=%s",(uid,))
	users = cursor.fetchall()
	if not users:
		user_update(db,uid)
		cursor.execute("SELECT scan_page,screen_name FROM weibo_user WHERE id=%s",(uid,))
		users = cursor.fetchall()

	#page为已经扫描到的页数
	page = users[0][0]

	if page<0:
		if restart:
			page = 1
		else:
			return
	else:
		page += 1

	not_ok_count = 0
	while True:
		#获取微博列表
		#global COUNT
		#COUNT += 1
		#if COUNT > 800:
		#	exit()

		data = client.getIndex_list(uid,page)
		#已扫描完退出，访问太频繁有几率不返回内容，故多请求几次
		if data['ok']==0 :
			if not_ok_count<2 :
				not_ok_count += 1
				time.sleep(not_ok_count)
				continue
			else :
				break
		
		data = data['data']
		print("user: %s page: %s" % (users[0][1],page))
		for card in data['cards']:
			if card['card_type']==9:
				id = card['mblog']['id']
				if 'retweeted_status' in card['mblog']:
					rid = card['mblog']['retweeted_status']['id']
					while not rid:
						print('retweeted_id is empty, try the other way, weibo_id: ' + id)
						rid = get_retweeted_status(id)
					cursor.execute("SELECT id FROM weibo_index WHERE id=%s",(rid,))
					if not cursor.fetchall():
						print(str(COUNT) + '. Updating retweeted_status: ' + users[0][1] + ' weibo_id: ' + id + '  ' + rid)
						weibo_insert(db,rid)

				cursor.execute("SELECT id FROM weibo_index WHERE id=%s",(id,))
				if not cursor.fetchall():
					print(str(COUNT) + '. Updating user: ' + users[0][1] + ' weibo_id: ' + id)
					weibo_insert(db,id)

		#更新扫描页面
		try:
			cursor.execute("UPDATE weibo_user SET scan_page=%s WHERE id=%s",(page,uid))
			db.commit()
		except:
			db.rollback()
			raise
		page += 1
		not_ok_count = 0
	#扫描完后scan_page设为负
	try:
		cursor.execute("UPDATE weibo_user SET scan_page=%s WHERE id=%s",(-page+1,uid))
		db.commit()
	except:
		db.rollback()
		raise

def get_retweeted_status(id):
	resStr = client._status(id)
	searchObj = re.search(r'var \$render_data = ([\s\S]*)\[0\] \|\| {};',resStr)
	if searchObj:
		res = searchObj.group(1)
		data = json.loads(res)[0]
		if 'retweeted_status' in data['status']:
			return data['status']['retweeted_status']['id']
		else:
			return None
	else:
		raise Exception('data error')
	

def weibo_insert(db,id):

	global COUNT
	COUNT += 1

	cursor = db.cursor()
	#未登录情况下访问频繁会403，已登录情况下访问频繁retweeted_status的id等内容会为空
	resStr = client._status(id)
	searchObj = re.search(r'var \$render_data = ([\s\S]*)\[0\] \|\| {};',resStr)
	if searchObj:
		res = searchObj.group(1)
		#data = json.loads(res)[0]
		#if 'retweeted_status' in data['status']:
		#	weibo_insert(db,data['status']['retweeted_status']['id'])
		

		with urllib.request.urlopen('http://localhost/weibo/api/insert_weibo.php',urllib.parse.urlencode({"data":res}).encode("ascii")) as f:
			returnStr = f.read().decode()
			returnObj = json.loads(returnStr)
			if returnObj['errorCode'] != "0" and returnObj['errorCode'] != "101":
				raise Exception(returnStr)
		'''
		if cursor.execute("SELECT id FROM weibo_index WHERE id=%s",(data['status']['id'],)):
			cursor.execute("UPDATE weibo_index SET " + reduce(lambda x,y:x+y,[k + "=%(" + k + ")s," for k in insert_data])[:-1] 
				+ " WHERE id=%(id)s",insert_data)
		else:
			cursor.execute("INSERT INTO weibo_index ( " + reduce(lambda x,y:x+y,[ k + "," for k in insert_data])[:-1] 
				+ " ) VALUES ( " + reduce(lambda x,y:x+y,[ "%(" + k + ")s," for k in insert_data])[:-1] + " )",insert_data)
		'''

if __name__ == '__main__':
	db = util.getDbConnect()
	user_list = util.getUserlist()
	for uid in user_list:
		scan_user_all(db,uid,restart=False)
		#user_weibo_update(db,uid,min_id="4282634743679613")
	db.close()
