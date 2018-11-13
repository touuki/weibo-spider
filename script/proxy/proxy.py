import urllib.request
import random
import abc

class Proxy:
	@abc.abstractmethod
	def get_proxy_handler(self):
		pass

class DefaultProxy(Proxy):
	def get_proxy_handler(self):
		return None

class LuminatiProxy(Proxy):
	def __init__(self,customer,zone,password,route_err='pass_dyn'):
		self.customer = customer
		self.zone = zone
		self.password = password
		self.route_err = route_err

	def get_proxy_handler(self,session = None):
		if session is None:
			session = '{:06d}'.format(random.randint(0,999999))
		username = 'lum-customer-{}-zone-{}-session-{}-route_err-{}'.format(self.customer,self.zone,session,self.route_err)
		proxy = 'http://{}:{}@zproxy.lum-superproxy.io:22225'.format(username,self.password)
		return urllib.request.ProxyHandler({'http':proxy,'https':proxy})