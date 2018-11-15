import datetime

s = 'Thu Nov 15 17:57:56 +0800 2018'

print(datetime.datetime.strptime(s, '%a %b %d %H:%M:%S %z %Y'))