from celery import Celery
app = Celery('task', broker='amqp://rabbit:tibbar@ubuntu18.uki.site//')
