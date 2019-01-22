from flask import Flask, jsonify, request, url_for
from worker import celery
import celery.states as states

app = Flask(__name__)


@app.route('/py/checkAuth', methods=['POST'])
def checkAuth():

    req = request.get_json()

    for attr in ["uid", "abs", "ords", "time"]:
        if attr not in req.keys():
            return 

    async_task = celery.send_task('tasks.process', args=[req], kwargs={})

    return jsonify({"taskid":async_task.id})


@app.route('/py/status/<task_id>', methods=['GET'])
def checkStatus(task_id):

    task = celery.AsyncResult(task_id)

    status = task.info.get('output')

    if status != 'FAILURE':
        response = {
            'state': status,
            'client': task.info.get('client')
        }
        
        if 'isAuthValid' in task.info:
            response['isAuthValid'] = task.info.get('isAuthValid', False)
    else: 
        # something went wrong in the background job
        response = {
            'state': 'FAILURE',     
            'client': task.info.get('client'),
            'msg': task.info.get('msg', ''),
            'isAuthValid': False # Invalid authentification
        }

    if status != 'PROGRESS':    # If task is finished, clear results
        task.forget()

    return jsonify(response)
