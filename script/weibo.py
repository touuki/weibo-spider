import http.cookiejar
import urllib.request,urllib.parse,urllib.error
import os, json, time, re, socket, ssl
import demjson

class MWeiboCn:
	def __init__(self,username,password,proxy_handler=None,cookie_file='weibo.cookie',
		normal_request_interval=1,error_request_interval=5,auto_retry=True,retry_times=5):

		self.error_count = 0
		self.normal_request_interval = normal_request_interval
		self.error_request_interval = error_request_interval
		self.auto_retry = auto_retry
		self.retry_times = retry_times

		self.debug_level = 0
		self.username = username
		self.password = password
		self.cookiejar = http.cookiejar.LWPCookieJar(cookie_file)
		if os.path.exists(cookie_file):
			self.cookiejar.load()
		cookie_support = urllib.request.HTTPCookieProcessor(self.cookiejar)
		self.opener = urllib.request.build_opener(cookie_support)
		self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'),
		('Accept','*/*'),
		('Accept-Language','zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3')
		]
		if proxy_handler:
			self.opener.add_handler(proxy_handler)
		self.update_st()

	def _send(self,url,data='',headers=[],method=''):
		'''http/https连接.返回字符串'''
		if isinstance(data, dict):
			delkeys = [key for key in data if data[key] is None]
			for key in delkeys:
				data.pop(key)
			data = urllib.parse.urlencode(data)
			if self.debug_level > 0 :
				print(data)
		for header in headers:
			self.opener.addheaders.append(header)

		if data:
			if method.upper() == 'GET':
				url = url + '?' + data
				data = None
			else:
				data = data.encode('ascii')
		else:
			data = None

		try:
			while True:
				try:
					response = self.opener.open(url,data)
					result = response.read().decode()
					self.error_count = 0
					time.sleep(self.normal_request_interval)            #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<时间间隔
					break
				except socket.timeout as e:
					self.error_count += 1
					if self.auto_retry and self.error_count <= self.retry_times:
						print("url %s timeout!" % (url,))
						time.sleep(self.error_request_interval)
					else:
						raise e
				except (urllib.error.URLError,ssl.SSLWantReadError) as e:
					self.error_count += 1
					if self.auto_retry and self.error_count <= self.retry_times:
						print(e)
						time.sleep(self.error_request_interval)
					else:
						raise e
				except urllib.error.HTTPError as e:
					self.error_count += 1
					if e.code == 400 and self.auto_retry and self.error_count <= self.retry_times:
						print(e)
						time.sleep(self.error_request_interval)
					else:
						raise e
		finally:		
			self.cookiejar.save()
			for header in headers:
				self.opener.addheaders.pop()
		return result

	def set_cookie(self, name, value, expires=None):
		'''手动设置cookie'''
		discard = False
		if expires is None:
			discard = True
		self.cookiejar.set_cookie(http.cookiejar.Cookie(
			version=0,
			name=name,
			value=value,
			port=None,
			port_specified=False,
			domain='.weibo.cn',
			domain_specified=True,
			domain_initial_dot=True,
			path='/',
			path_specified=True,
			secure=False,
			expires=expires,
			discard=discard,
			comment=None,
			comment_url=None,
			rest={}
		))
		self.cookiejar.save()

	def is_logined(self):
		'''判断登录'''
		#self.update_st()
		return True if self.st else False

	def login(self):
		'''
		登录,暂未处理验证问题
		request = urllib.request.Request('https://m.weibo.cn')
		res = urllib.request.urlopen(request)

		request = urllib.request.Request('https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=http://m.weibo.cn/')
		res = urllib.request.urlopen(request)

		request = urllib.request.Request('https://login.sina.com.cn/sso/prelogin.php?checkpin=1&entry=mweibo&su=' + utf8_to_b64(username).decode('ascii'))
		res = urllib.request.urlopen(request)
		'''
		data={'username':self.username,
		'password':self.password,
		'savestate':'1',
		'r':'http://m.weibo.cn/',
		'ec':'0',
		#'pagerefer':'https://passport.weibo.cn/signin/welcome?entry=mweibo&r=http%3A%2F%2Fm.weibo.cn%2F',
		'pagerefer':'',
		'entry':'mweibo',
		'wentry':'',
		'loginfrom':'',
		'client_id':'',
		'code':'',
		'qq':'',
		'mainpageflag':'1',
		'hff':'',
		'hfp':''}
		headers = [('Referer','https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=http%3A%2F%2Fm.weibo.cn%2F')]
		result = self._send('https://passport.weibo.cn/sso/login',data,headers)
		if self.debug_level > 0:
			print(result)
		result_data=json.loads(result)
		weibo_com_url = result_data['data']['crossdomainlist']['weibo.com']
		sina_com_cn_url = result_data['data']['crossdomainlist']['sina.com.cn']
		weibo_cn_url = result_data['data']['crossdomainlist']['weibo.cn']
		self._send(weibo_com_url)
		self._send(sina_com_cn_url)
		self._send(weibo_cn_url)
		self.update_st()

	def _getIndex_contents(self,uid,page):
		'''return json string. 微博用户的列表'''
		data={'uid':uid,'containerid':'107603%s' % uid,'page':page}
		return self._send('https://m.weibo.cn/api/container/getIndex',data,method='GET')

	def getIndex_contents(self,uid,page):
		result = self._getIndex_contents(uid,page)
		result_data = json.loads(result)
		return result_data
		
	def _getIndex_user(self,uid):
		'''return json string. 微博用户信息'''
		data={'uid':uid,'containerid':'100505%s' % uid}
		return self._send('https://m.weibo.cn/api/container/getIndex',data,method='GET')
		
	def _status(self,id):
		'''return json string. 单条微博信息'''
		#return self._send('https://m.weibo.cn/detail/%s' % id)
		return self._send('https://m.weibo.cn/status/%s' % id)

	def status(self,id,decode=True):
		result = self._status(id)
		search = re.search(r'var \$render_data = \[([\s\S]*)\]\[0\] \|\| {};',result)
		if search:
			if decode:
				return json.loads(search.group(1))
			else:
				return search.group(1)
		else:
			return None

	def attitudes_show(self,id,page):
		'''return json string. 微博点赞'''
		data={'id':id,'page':page}
		return self._send('https://m.weibo.cn/api/attitudes/show',data,method='GET')

	def comments_show(self,id,page):
		'''return json string. 微博评论'''
		data={'id':id,'page':page}
		return self._send('https://m.weibo.cn/api/comments/show',data,method='GET')

	def statuses_repostTimeline(self,id,page):
		'''return json string. 微博转发'''
		data={'id':id,'page':page}
		return self._send('https://m.weibo.cn/api/statuses/repostTimeline',data,method='GET')

	def unread(self):
		'''return json string. eg. {"qp":{"new":10,"sx":35},"ht":{"sx":35}}  主页的'''
		if not self.st:
			self.login()
		data={'t':int(time.time()*1000)}
		return self._send('https://m.weibo.cn/unread',data,method='GET')

	def index_getCommonGroup(self):
		'''eg. {"ok":1,"data":[{"gid":"4136673992986449","title":"snh48"}]}'''
		if not self.st:
			self.login()
		return self._send('https://m.weibo.cn/index/getCommonGroup')

	def index_group(self,gid,next_cursor=None,page=None):
		'''从next_cursor开始的第page页,不传入next_cursor则从最新处起算'''
		if not self.st:
			self.login()
		data={'format':'cards','gid':gid,'next_cursor':next_cursor,'page':page}
		return self._send('https://m.weibo.cn/index/group',data,method='GET')

	def home_groupList(self):
		if not self.st:
			self.login()
		result = self._send('https://m.weibo.cn/home/groupList')
		search = re.search(r'window\.\$render_data = ([\s\S]*?);</script>',result)
		if search:
			return search.group(1)
		else:
			return None

	#@depercated
	def shift_group(self,group_name):
		data = json.loads(self.home_groupList())
		for group in data['stage']['groupList']:
			if group.get('card_type')==11:
				for card_group in group['card_group']:
					if card_group['desc1'] == group_name:
						self._send('https://m.weibo.cn' + card_group['scheme'])

	#@depercated
	def shift_to_all(self):
		if not self.st:
			self.login()
		result_data = self.home_render_data()
		self.set_cookie('H5_INDEX','0_all')
		self.set_cookie('H5_INDEX_TITLE',urllib.parse.quote(result_data['stage']['home'][0]['userName']))

	def home_render_data(self):
		result = self._send('https://m.weibo.cn')
		search = re.search(r'window\.\$render_data = ([\s\S]*?);</script>',result)
		return demjson.decode(search.group(1))

	def config(self):
		'''{"login":true,"st":"a64cf0","uid":"5853763310"}'''
		return self._send('https://m.weibo.cn/api/config')

	def update_st(self):
		result_data = json.loads(self.config())
		if result_data['data']['login']:
			self.st = result_data['data']['st']
		else:
			self.st = None
		return self.st

	def _comments_create(self,id,content,st):
		'''创建评论'''
		mid = id
		data={'id':id,'content':content,'mid':mid, 'st':st}
		headers = [('Origin','https://m.weibo.cn'),
			('Referer','https://m.weibo.cn/compose/comment?id=%s' % id)]
		return self._send('https://m.weibo.cn/api/comments/create',data,headers)

	def comment(self,id,content):
		self.update_st()
		result = self._comments_create(id,content,self.st)
		result_data = json.loads(result)
		return result_data

	def _statuses_repost(self,id,content,st):
		'''转发'''
		mid = id
		data={'id':id,'content':content,'mid':mid, 'st':st}
		return self._send('https://m.weibo.cn/api/statuses/repost',data)

	def _attitudes_create(self,id,st):
		'''微博点赞'''
		data={'id':id,'attitude':'heart', 'st':st}
		headers = [('Origin','https://m.weibo.cn'),
			('Referer','https://m.weibo.cn/status/%s' % id)]
		return self._send('https://m.weibo.cn/api/attitudes/create',data,headers)

	def _attitudes_destroy(self,id,st):
		'''微博取消赞'''
		data={'id':id,'attitude':'heart', 'st':st}
		headers = [('Origin','https://m.weibo.cn'),
			('Referer','https://m.weibo.cn/status/%s' % id)]
		return self._send('https://m.weibo.cn/api/attitudes/create',data,headers)

	def _attitudesDeal_add(self,id,st):
		'''微博点赞,与_attitudes_create相同'''
		data={'id':id,'attitude':'heart','st':st}
		headers = [('Origin','https://m.weibo.cn'),
			('Referer','https://m.weibo.cn/')]
		return self._send('https://m.weibo.cn/attitudesDeal/add',data,headers)

	def _attitudesDeal_delete(self,id,st):
		'''微博取消赞,与_attitudes_destroy相同'''
		data={'id':id,'st':st}
		headers = [('Origin','https://m.weibo.cn'),
			('Referer','https://m.weibo.cn/')]
		return self._send('https://m.weibo.cn/attitudesDeal/delete',data,headers)

	def feed_friends(self,version='v4',next_cursor=None,page=None):
		'''主页时间线，版本v4和默认传回的数据结构不一样，从next_cursor开始的第page页,不传入next_cursor则从最新处起算'''
		data={'version':version,'next_cursor':next_cursor,'page':page}
		return self._send('https://m.weibo.cn/feed/friends',data,method='GET')

	def _update(self,content,st):
		'''发微博'''
		data={'content':content, 'st':st}
		headers = [('Origin','https://m.weibo.cn'),
			('Referer','https://m.weibo.cn/compose')]
		return self._send('https://m.weibo.cn/api/statuses/update',data,headers)

	def update(self,content):
		self.update_st()
		result = self._update(content,self.st)
		result_data = json.loads(result)
		return result_data

	def delMyMblog(self,id):
		'''删除微博'''
		data={'id':id}
		headers = [('Origin','https://m.weibo.cn'),
			('Referer','https://m.weibo.cn')]
		return self._send('https://m.weibo.cn/mblogDeal/delMyMblog',data,headers)
