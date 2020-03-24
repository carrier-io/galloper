#     Copyright 2020 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import os
from uuid import uuid4

from flask import Blueprint, request, render_template, flash, current_app, redirect, url_for
from sqlalchemy import and_
from werkzeug.utils import secure_filename

from galloper.constants import allowed_file, NAME_CONTAINER_MAPPING
from control_tower import run

from galloper.database.models.project import Project
from galloper.database.models.task import Task
from galloper.database.models.task_results import Results
from galloper.utils.auth import project_required

bp = Blueprint("tasks", __name__)


@bp.route("/tasks", methods=["GET"])
@project_required
def tasks(project: Project):
    tasks_ = Task.query.filter(Task.project_id == project.id).order_by(Task.id).all()
    return render_template("lambdas/tasks.html", tasks=tasks_, project_id=project.id)


@bp.route("/task/<string:task_id>", methods=["GET", "POST"])
def call_lambda(task_id: str):
    if request.method == "POST":
        if request.content_type == "application/json":
            task = Task.query.filter(
                and_(Task.task_id == task_id)
            ).first().to_json()
            event = request.get_json()
            app = run.connect_to_celery(1)
            celery_task = app.signature("tasks.execute",
                                        kwargs={"task": task, "event": event})
            celery_task.apply_async()
            return "Accepted", 201
        elif request.content_type == "application/x-www-form-urlencoded":
            return f"Calling {task_id} with {request.form}"

    task = Task.query.filter(
        and_(Task.task_id == task_id)
    ).first()
    return render_template(
        "lambdas/task.html",
        task=task,
        runtimes=NAME_CONTAINER_MAPPING.keys()
    )


@bp.route("/task", methods=["GET", "POST"])
@project_required
def add_task(project: Project):
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return ""
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return ""
        if file and allowed_file(file.filename):
            filename = str(uuid4())
            filename = secure_filename(filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            app = run.connect_to_celery(1)
            celery_task = app.signature(
                "tasks.volume",
                kwargs={"task_id": filename, "file_path": current_app.config["UPLOAD_FOLDER"]}
            )
            celery_task.apply_async()
            task = Task(
                task_id=filename,
                project_id=project.id,
                zippath=filename,
                task_name=request.form["funcname"],
                task_handler=request.form["invoke_func"],
                runtime=request.form["runtime"],
                env_vars=request.form["env_vars"]
            )
            task.insert()
            return f"{filename}"

    return render_template("lambdas/add_task.html", runtimes=NAME_CONTAINER_MAPPING.keys())


@bp.route("/task/<string:task_id>/<string:action>", methods=["GET", "POST"])
@project_required
def suspend_task(project: Project, task_id: str, action: str):
    if action in ("suspend", "delete", "activate"):
        task = Task.query.filter(
                and_(Task.task_id == task_id, Task.project_id == project.id)
            ).first()
        getattr(task, action)()
    elif action == "edit":
        if request.method == "POST":
            task = Task.query.filter(
                and_(Task.task_id == task_id, Task.project_id == project.id)
            ).first()
            for key, value in request.form.items():
                if key in ["id", "task_id", "zippath", "last_run"]:
                    continue
                elem = getattr(task, key, None)
                if value in ["None", "none", ""]:
                    value = None
                if elem != value:
                    setattr(task, key, value)
                task.commit()
            return "OK", 201

        return "Data is miss-formatted", 200

    elif action == "results":
        if request.method == "POST":
            data = request.get_json()
            task = Task.query.filter(
                and_(Task.task_id == task_id, Task.project_id == project.id)
            ).first()
            task.set_last_run(data["ts"])
            result = Results(task_id=task_id,
                             ts=data["ts"],
                             results=data["results"],
                             log=data["stderr"])
            result.insert()
            return "OK", 201

        result = Results.query.filter(
            and_(Results.task_id == task_id, Task.project_id == project.id)
        ).order_by(Results.ts.desc()).all()
        task = Task.query.filter(
            and_(Task.task_id == task_id, Task.project_id == project.id)
        ).first()
        return render_template("lambdas/task_results.html", results=result, task=task)

    return redirect(url_for("tasks.tasks"))
