import config
import subprocess
import pipes
import multiprocessing
import time
import os

def download(pid,url,dr):
	db = config.get_db_connect()
	cursor = db.cursor()
	try:
		file_dir = "/var/www/html/weibo/image/%s/%s" % (dr,pid[:12])		
		if not os.path.exists(file_dir):
			os.mkdir(file_dir)
		typ = url[url.rindex(r'.') + 1:]
		filepath = "%s/%s.%s" % (file_dir,pid,typ)
		exitcode = subprocess.call("wget --max-redirect=0 -q -O %s %s" % (pipes.quote(filepath),pipes.quote(url)),shell=True)
		if exitcode == 0:
			cursor.execute("UPDATE weibo_pic_" + dr + " SET status=%s WHERE pid=%s",(1,pid))
		elif exitcode == 8:
			pass
			#cursor.execute("UPDATE weibo_pic_" + dr + " SET status=%s WHERE pid=%s",(2,pid))
		db.commit()
	except:
		db.rollback()
		raise
	finally:
		cursor.close()
		db.close()


num_pro = 10
pool = multiprocessing.Pool(processes = num_pro)
db = config.get_db_connect()
cursor = db.cursor()
cursor.execute("SELECT pid,url FROM weibo_pic_orj360 WHERE status=2")
pics = cursor.fetchall()
for pid,url in pics:
	pool.apply_async(download,(pid,url,"orj360"))

cursor.execute("SELECT pid,url FROM weibo_pic_large WHERE status=2")
pics = cursor.fetchall()
for pid,url in pics:
	pool.apply_async(download,(pid,url,"large"))

db.close()
pool.close()
pool.join()

