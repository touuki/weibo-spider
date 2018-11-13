import configparser
import os
cf = configparser.ConfigParser()
cf.read(os.path.join(os.path.dirname(__file__),'../config/config.default.ini'))
cf.read(os.path.join(os.path.dirname(__file__),'config.test.ini'))
print(cf.getint('db','host'))