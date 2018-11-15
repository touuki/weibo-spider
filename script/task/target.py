import traceback
import json, re
import time
from functools import reduce
import urllib.request
import socket
from weibo import MWeiboCn
from .workers import app

socket.setdefaulttimeout(5)
global _client
_client = None

def get_client():
	global _client
	if _client is None:
		#get from control
		_client = MWeiboCn()
	return _client

@app.task
def user_update(id):
	res = client._getIndex_user(id)
	control.user_update.delay(res)

@app.task
def weibo_api(id,operation='insert'):
	client = get_client()
	content = client.status(id,decode=False)
	if content is not None:
		control.operate.delay(content,operation)

@app.task
def scan_page(uid,page,min_id = 0, request_count = 1, update_scan_page = False):
	client = get_client()
	data = client.getIndex_contents(uid,page)
	#已扫描完退出，访问太频繁有几率不返回内容，故多请求几次
	if data['ok'] == 0:
		if request_count < 3:
			request_count += 1
			time.sleep(request_count)
			scan_page.delay(uid,page,min_id = min_id,request_count = request_count + 1)
		else:
			control.update_max_mid.delay(uid)
			return False

	data = data['data']
	print("user: %s page: %s" % (uid,page))
	for card in data['cards']:
		if card['card_type']==9:
			id = card['mblog']['id']
			if int(id) < int(min_id) and 'isTop' not in card['mblog']:
				control.update_max_mid.delay(uid)
				return False

			if 'retweeted_status' in card['mblog']:
				retweeted_status = card['mblog']['retweeted_status']
				#未登录情况下访问频繁会403，较久远微博retweeted_status的id等内容有时会为空
				while not retweeted_status['id']:
					print('retweeted_id is empty, try the other way, weibo_id: ' + id)
					retweeted_status = get_retweeted_status(id)
				control.single_weibo.delay(retweeted_status)

			control.single_weibo.delay(card['mblog'])

	if update_scan_page:
		control.update_scan_page.delay()
	scan_page.delay(uid,page + 1,min_id = min_id)

def get_retweeted_status(id):
	client = get_client()
	data = client.status(id)
	if data is None:
		raise Exception('data error')
	else:
		if 'retweeted_status' in data['status']:
			return data['status']['retweeted_status']
		else:
			return None

@app.task
def test(id):
	client = get_client()
	return client.status(id)