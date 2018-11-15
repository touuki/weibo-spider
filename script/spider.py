import traceback
import json, re
import time
from weibo import MWeiboCn
from functools import reduce
import urllib.request
import socket
import config
from celery import Celery
app = Celery('test', broker='amqp://rabbit:tibbar@ubuntu18.uki.site//')


socket.setdefaulttimeout(5)
global count
count = 0
client = config.get_weibo_client()
if not client.st:
	client.login()



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


if __name__ == '__main__':
	db = config.get_db_connect()
	users = config.get_scan_users()
	for uid in users:
		#scan_user_all(db,uid,restart=False)
		user_weibo_update(db,uid)
	db.close()
