import config
import os
import shutil

large_path = '/var/www/html/weibo/image/large'
orj360_path = '/var/www/html/weibo/image/orj360'

def move(pid,typ):
	large_dir = '%s/%s' % (large_path, pid[:12])
	orj360_dir = '%s/%s' % (orj360_path, pid[:12])
	if not os.path.exists(orj360_dir):
		os.mkdir(orj360_dir)
	if not os.path.exists(large_dir):
		os.mkdir(large_dir)
	shutil.move('{}/{}.{}'.format(orj360_path,pid,typ),'{}/{}.{}'.format(orj360_dir,pid,typ))
	shutil.move('{}/{}.{}'.format(large_path,pid,typ),'{}/{}.{}'.format(large_dir,pid,typ))
	try:
		cursor.execute("UPDATE weibo_pic_orj360 SET status=3 WHERE pid=%s",(pid,))
		cursor.execute("UPDATE weibo_pic_large SET status=3 WHERE pid=%s",(pid,))
		db.commit()
	except:
		db.rollback()
		raise


db = config.get_db_connect()
cursor = db.cursor()

try:
	while cursor.execute("SELECT a.pid,a.type FROM weibo_pic a JOIN weibo_pic_orj360 b JOIN weibo_pic_large c ON a.pid=b.pid \
	 AND a.pid=c.pid WHERE b.status=1 AND c.status=1 LIMIT 1000"):
		for pid,typ in cursor.fetchall():
			move(pid,typ)
finally:
	cursor.close()
	db.close()
