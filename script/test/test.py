import urllib.request
x = 1

def f2():
	return x

def f1(a=f2()):
	print(a)

x = 2
f1()