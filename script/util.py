import pymysql
import weibo
import configparser
import os

global cf,cfdict

def config():
	global cf,cfdict
	cf = configparser.ConfigParser()
	dirname, _ = os.path.split(os.path.abspath(__file__))
	cf.read('%s/config.ini' % (dirname,))
	cfdict = {}
	for section in cf.sections():
		cfdict[section] = {}
		for key,val in cf.items(section):
			cfdict[section][key] = val

def getDbConnect():
	global cfdict
	dbconfig = cfdict['db']
	return pymysql.connect(dbconfig['host'],dbconfig['username'],dbconfig['password'],dbconfig['dbname'],port=dbconfig['port'],charset=dbconfig['charset'])

def getWeiboClient():
	global cfdict
	wbConfig = cfdict['weibo']
	return weibo.MWeiboCn(wbConfig['username'],wbConfig['password'])

def getUserlist():
	global cfdict
	scanConfig = cfdict['scan']
	return scanConfig['userlist'].split(',')

config()
