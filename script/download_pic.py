import subprocess
import pipes
import multiprocessing
import time
import config

def download(pid,url,dr):
	db = config.get_db_connect()
	cursor = db.cursor()
	try:
		typ = url[url.rindex(r'.'):]
		filename = pid + typ
		filepath = "/var/www/html/weibo/image/%s/%s" % (dr,filename)
		exitcode = subprocess.call("wget --max-redirect=0 -q -O %s %s" % (pipes.quote(filepath),pipes.quote(url)),shell=True)
		if exitcode == 0:
			cursor.execute("UPDATE weibo_pic_" + dr + " SET status=%s WHERE pid=%s",(1,pid))
		elif exitcode == 8:
			cursor.execute("UPDATE weibo_pic_" + dr + " SET status=%s WHERE pid=%s",(2,pid))
		db.commit()
	except:
		db.rollback()
		raise
	db.close()

num_pro = 10
while True:
	pool = multiprocessing.Pool(processes = num_pro)
	db = config.get_db_connect()
	cursor = db.cursor()
	cursor.execute("SELECT pid,url FROM weibo_pic_orj360 WHERE status=0 LIMIT 300")
	pics = cursor.fetchall()
	for pid,url in pics:
		pool.apply_async(download,(pid,url,"orj360"))
	
	cursor.execute("SELECT pid,url FROM weibo_pic_large WHERE status=0 LIMIT 300")
	pics = cursor.fetchall()
	for pid,url in pics:
		pool.apply_async(download,(pid,url,"large"))

	db.close()
	pool.close()
	pool.join()
	time.sleep(5)


