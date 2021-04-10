from celery import Celery
from google.transit.gtfs_realtime_pb2 import FeedMessage
import requests
import os

app = Celery(__name__,
             backend=os.environ["CELERY_REDIS"],
             broker=os.environ["CELERY_REDIS"],)

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    print('Setting up periodic tasks')
    sender.add_periodic_task(10.0, check.s(), name='check every 10')
    print('Done periodic tasks')

@app.task
def check():
    print("Aloha")