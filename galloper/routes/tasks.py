#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
from uuid import uuid4
from datetime import datetime

from flask import Blueprint, request, render_template, flash, current_app, redirect, url_for
from werkzeug.utils import secure_filename

from galloper.constants import allowed_file
from galloper.models.task import Task
from galloper.models.task_results import Results
from control_tower import run


bp = Blueprint('tasks', __name__)


@bp.route('/tasks', methods=["GET", "POST"])
def tasks():
    if request.method == "GET":
        tasks = Task.query.order_by(Task.id).all()
        return render_template('lambdas/tasks.html', tasks=tasks)


@bp.route('/task', methods=["GET", "POST"])
def add_task():
    if request.method == 'GET':
        return render_template('lambdas/add_task.html')
    if request.method == 'POST':
        print(request.form)
        if 'file' not in request.files:
            flash('No file part')
            return ''
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return ''
        if file and allowed_file(file.filename):
            filename = str(uuid4())
            filename = secure_filename(filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            app = run.connect_to_celery(1)
            celery_task = app.signature('tasks.volume',
                                        kwargs={'task_id': filename, 'file_path': current_app.config['UPLOAD_FOLDER']})
            celery_task.apply_async()
            task = Task(task_id=filename, zippath=filename, task_name=request.form['funcname'],
                        task_handler=request.form['invoke_func'], runtime=request.form['runtime'])
            task.insert()
            return f"{filename}"


@bp.route('/task/<task_name>', methods=["GET", "POST"])
def call_lambda(task_name):
    if request.method == "GET":
        return render_template("lambdas/task.html", task=Task.query.filter_by(task_id=task_name).first())
    else:
        print(request.content_type)
        if request.content_type == "application/json":
            task = Task.query.filter_by(task_id=task_name).first().to_json()
            print(task)
            event = request.get_json()
            print(event)
            app = run.connect_to_celery(1)
            celery_task = app.signature('tasks.execute',
                                        kwargs={'task': task, 'event': event})
            celery_task.apply_async()
            return "Accepted", 201
        elif request.content_type == "application/x-www-form-urlencoded":
            return f"Calling {task_name} with {request.form}"


@bp.route('/task/<task_name>/<action>', methods=["GET", "POST"])
def suspend_task(task_name, action):
    if action in ['suspend', 'delete', 'activate']:
        task = Task.query.filter_by(task_id=task_name).first()
        getattr(task, action)()
    elif action == 'edit':
        if request.method == 'POST':
            task = Task.query.filter_by(task_id=task_name).first()
            for key, value in request.form.items():
                if key in ['id', 'task_id', 'zippath', 'last_run']:
                    continue
                elem = getattr(task, key, None)
                if value in ['None', 'none', '']:
                    value = None
                if elem != value:
                    setattr(task, key, value)
                task.commit()
            return "OK", 201
        return "Data is miss-formatted", 200
    elif action == 'results':
        if request.method == 'POST':
            data = request.get_json()
            task = Task.query.filter_by(task_id=task_name).first()
            task.set_last_run(data['ts'])
            result = Results(task_id=task_name, ts=data['ts'],
                             results=data['results'],
                             log=data['stderr'])
            result.insert()
            return "OK", 201
        if request.method == 'GET':
            result = Results.query.filter_by(task_id=task_name).order_by(Results.ts.desc()).all()
            task = Task.query.filter_by(task_id=task_name).first()
            return render_template('lambdas/task_results.html', results=result, task=task)
    return redirect(url_for('tasks.tasks'))


@bp.route('/', methods=['GET'])
def index():
    if request.method == "GET":
        return render_template('lambdas/tasks.html')
