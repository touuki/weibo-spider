from . import generator as _generator

def get_generator(name='None',*args,**kwargs):
	generator = getattr(_generator, '{}Generator'.format(name))
	assert issubclass(generator, _generator.Generator)
	return generator(*args,**kwargs)
