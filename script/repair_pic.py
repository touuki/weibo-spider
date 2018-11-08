import util
import subprocess
import pipes
import multiprocessing
import time

def download(pid,url,dr):
	db = util.getDbConnect()
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
pool = multiprocessing.Pool(processes = num_pro)
db = util.getDbConnect()
cursor = db.cursor()
cursor.execute("SELECT pid,url FROM weibo_pic_orj360 WHERE status=2")
pic_list = cursor.fetchall()
for pid,url in pic_list:
	pool.apply_async(download,(pid,url,"orj360"))

cursor.execute("SELECT pid,url FROM weibo_pic_large WHERE status=2")
pic_list = cursor.fetchall()
for pid,url in pic_list:
	pool.apply_async(download,(pid,url,"large"))

db.close()
pool.close()
pool.join()

