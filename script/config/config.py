import pymysql
import weibo
import configparser
import os

dirname, _ = os.path.split(os.path.abspath(__file__))
default_filepath = '%s/config.ini' % (dirname,)

class Config:
	def __init__(self,filepath = None):
		self._config = {
				'db':{
					'host':'localhost',
					'username':'root',
					'password':'123456',
					'port':3306,
					'dbname':'WEIBO',
					'charset':'utf8mb4'
					},
				'weibo':{
					'username':'',
					'password':''
					},
				'scan':{
					'userlist':'',
					'normal_interval':1,
					'error_interval':5,
					'confirm_num':6
					}
				}

		cf = configparser.ConfigParser()
		if filepath is None:
			cf.read(default_filepath)
		else:
			cf.read(filepath)
		for section in cf.sections():
			if section in self._config:
				for key,val in cf.items(section):
					self._config[section][key] = val
			else:
				print('WARING: Section %s is unused in config file.' % (section,))

	def get(self,section = None, key = None):
		if section is None:
			return self._config
		else:
			if key is None:
				return self._config[section]
			else:
				return self._config[section][key]

	def getDbConnect(self):
		db = self._config['db']
		return pymysql.connect(db['host'],db['username'],db['password'],db['dbname'],port=db['port'],charset=db['charset'])

	def getWeiboClient(self):
		wb = self._config['weibo']
		return weibo.MWeiboCn(wb['username'],wb['password'])

	def getUserlist(self):
		return self._config['scan']['userlist'].split(',')

default = Config() 
