import proxy as _proxy

def get_proxy(class_name='DefaultProxy',*args,**kwargs):
	proxy = getattr(_proxy, class_name)
	assert ischildof(proxy, _proxy.Proxy)
	return proxy(*args,**kwargs)