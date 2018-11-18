import pymysql
import weibo
import configparser
import os
import sys
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
	global _proxy_generator
	proxy_type = _cf.get('job','proxy')
	if _proxy_generator is None:
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
	return _cf.get('job','scan_users').split(',')

def get_weibo_client():
	return weibo.MWeiboCn(
		username=_cf.get('job','weibo_username'),
		password=_cf.get('job','weibo_password'),
		proxy_handler=get_proxy_generator().get(),
		cookie_file=_cf.get('job','cookie_file'),
		normal_request_interval=_cf.getint('weibo_options','normal_request_interval'),
		error_request_interval=_cf.getint('weibo_options','error_request_interval'),
		auto_retry=_cf.getboolean('weibo_options','auto_retry'),
		retry_times=_cf.getint('weibo_options','retry_times')
		)

