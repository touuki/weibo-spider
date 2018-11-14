import urllib.request
import random
import abc

class Generator:
	@abc.abstractmethod
	def get(self):
		pass

class NoneGenerator(Generator):
	def get(self):
		return None

class LuminatiGenerator(Generator):
	def __init__(self,customer,zone,password,route_err='pass_dyn'):
		self.customer = customer
		self.zone = zone
		self.password = password
		self.route_err = route_err

	def get(self,session = None):
		if session is None:
			session = '{:06d}'.format(random.randint(0,999999))
		username = 'lum-customer-{}-zone-{}-session-{}-route_err-{}'.format(self.customer,self.zone,session,self.route_err)
		proxy = 'http://{}:{}@zproxy.lum-superproxy.io:22225'.format(username,self.password)
		return urllib.request.ProxyHandler({'http':proxy,'https':proxy})