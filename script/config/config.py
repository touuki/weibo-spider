import pymysql
import weibo
import configparser
import os

global _config
_default_filepath = os.path.join(os.path.dirname(__file__),'config.ini')

def default_init():
	global _config
	_config = {}
	cf = configparser.ConfigParser()
	cf.read(os.path.join(os.path.dirname(__file__),'config.default.ini'))
	for section in cf.sections():
		_config[section] = {}
		for key,val in cf.items(section):
			_config[section][key] = val	

def init(filepath = None):
	global _config
	default_init()
	cf = configparser.ConfigParser()
	if filepath is None:
		cf.read(_default_filepath)
	else:
		cf.read(filepath)
	for section in cf.sections():
		if section in _config:
			for key,val in cf.items(section):
				_config[section][key] = val
		else:
			print('WARING: Section %s is unused in config file.' % (section,))

def get(section = None, key = None):
	if section is None:
		return _config
	else:
		if key is None:
			return _config[section]
		else:
			return _config[section][key]

def get_int(section, key):
	return int(get(section,key))

def get_db_connect():
	db = _config['db']
	return pymysql.connect(db['host'],db['username'],db['password'],db['dbname'],port=db['port'],charset=db['charset'])

def get_weibo_client():
	wb = _config['weibo']
	return weibo.MWeiboCn(wb['username'],wb['password'])

def get_scan_users():
	return _config['scan']['users'].split(',')

