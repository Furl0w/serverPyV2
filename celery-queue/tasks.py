import os
import time
from celery import Celery
import processing as proc
import requests, json

SERVER_GO_URL = 'http://serverauth:3030'
SERVER_DB_URL = 'http://serverdb:3031'

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379')

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery.task(name='tasks.add')
def add(x, y):
    return x + y


@celery.task(name='tasks.process', bind=True, time_limit=60)
def process(self, req):

    self.update_state(state='PROGRESS', meta={
        "client": req['uid'],
        "output" : 'PROGRESS'
    })

    user = getUserSignatures(req['uid'])

    meta = { "client": req['uid'] }

    if(user is None):
        meta = {
            "client": req['uid'],
            "output" : 'FAILURE',
            "isAuthValid" : False,
            "msg" : "invalid user id"
        }

    else:

        try:
            meta["isAuthValid"] = proc.process(req, user)
            # meta["isAuthValid"] = proc_ml.process(req, user)
        except:
            meta = {
                "client": req['uid'],
                "output" : 'FAILURE',
                "isAuthValid" : False,
                "msg" : "Error while computing values",
            }
    if(meta["isAuthValid"]==True):
        try:
            requests.post(f'{SERVER_GO_URL}/authAnswer', data=json.dumps({
                "client": req['uid'],
                "isAuthValid": meta["isAuthValid"]
            }), headers={'Content-Type': 'application/json'})
            meta["output"] = "SUCCESS"

        except:
            meta = {
                "client": req['uid'],
                "output" : 'FAILURE',
                "isAuthValid": False,
                "msg": "communication with auth server failed"
            }

        finally:
            return meta
    return meta


def getUserSignatures(uid):

    res = requests.get(f'{SERVER_DB_URL}/user/email/{uid}')
    return res.json()[0]["signatures"]
