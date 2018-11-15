from celery import Celery

app = Celery('test', broker='amqp://rabbit:tibbar@ubuntu18.uki.site//')

@app.task
def hello():
    add.delay(app,[2,3])
    return 'hello world'

@app.task
def add(x, y):
    return x