import pymysql
import weibo
import configparser
import os

global _cf
_cf = configparser.ConfigParser()

def default_init():
	_cf.read(os.path.join(os.path.dirname(__file__),'config.default.ini'))

def init(filepath = None):
	default_init()
	if filepath is None:
		_cf.read(os.path.join(os.path.dirname(__file__),'config.ini'))
	else:
		_cf.read(filepath)

def get_parser():
	return _cf

def get_db_connect():
	return pymysql.connect(_cf.get('db','host'),_cf.get('db','username'),_cf.get('db','password'),_cf.get('db','dbname'),port=_cf.getint('db','port'),charset=_cf.get('db','charset'))

def get_weibo_client():
	return weibo.MWeiboCn(_cf.get('weibo','username'),_cf.get('weibo','password'))

def get_scan_users():
	return _cf.get('scan','users').split(',')

