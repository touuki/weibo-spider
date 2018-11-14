import pymysql
import weibo
import configparser
import os
import sys
sys.path.append('..')
import proxy

global _cf,_proxy_generator

def default_init():
	global _cf,_proxy_generator
	_cf = configparser.ConfigParser()
	_proxy_generator = None
	_cf.read(os.path.join(os.path.dirname(__file__),'config.default.ini'))

def init(filepath = None):
	default_init()
	if filepath is None:
		_cf.read(os.path.join(os.path.dirname(__file__),'config.ini'))
	else:
		_cf.read(filepath)

def get_session(section = None):
	data = {}
	if section in _cf.sections():
		for key,val in _cf.items(section):
			data[key] = val
		return data
	else:
		return None

def get_proxy_generator():
	proxy_type = _cf.get('job','proxy')
	if _proxy_generator is None:
		global _proxy_generator
		if proxy_type == 'None':
			_proxy_generator = proxy.get_generator()
		else:
			_proxy_generator = proxy.get_generator(proxy_type,**get_session(proxy_type.lower()))
	return _proxy_generator

def get_parser():
	return _cf

def get_db_connect():
	return pymysql.connect(_cf.get('db','host'),_cf.get('db','username'),_cf.get('db','password'),_cf.get('db','dbname'),port=_cf.getint('db','port'),charset=_cf.get('db','charset'))

def get_scan_users():
	return _cf.get('job','users').split(',')

def get_weibo_client():
	return weibo.MWeiboCn(
		username=_cf.get('job','username'),
		password=_cf.get('job','password'),
		proxy_handler=get_proxy_generator().get(),
		cookie_file=_cf.get('job','cookie_file'),
		**get_session('weibo_options')
		)

