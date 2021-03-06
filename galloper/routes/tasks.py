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

from flask import Blueprint, request, render_template, redirect, url_for
from sqlalchemy import and_


from galloper.constants import NAME_CONTAINER_MAPPING, RABBIT_QUEUE_NAME

from galloper.database.models.project import Project
from galloper.database.models.task import Task
from galloper.database.models.statistic import Statistic
from galloper.api.base import check_tasks_quota
from galloper.utils.auth import project_required
from galloper.api.base import get_arbiter
from galloper.dal.vault import unsecret

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
            check_tasks_quota(task)
            statistic = Statistic.query.filter(Statistic.project_id == task['project_id']).first()
            setattr(statistic, 'tasks_executions', Statistic.tasks_executions + 1)
            statistic.commit()
            event = request.get_json()
            arbiter = get_arbiter()
            task_kwargs = {"task": task, "event": event,
                           "galloper_url": unsecret("{{secret.galloper_url}}", project_id=task['project_id']),
                           "token": unsecret("{{secret.auth_token}}", project_id=task['project_id'])}
            arbiter.apply("execute_lambda", queue=RABBIT_QUEUE_NAME, task_kwargs=task_kwargs)
            arbiter.close()
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


@bp.route("/task", methods=["GET"])
@project_required
def add_task(project: Project):
    return render_template("lambdas/add_task.html", runtimes=NAME_CONTAINER_MAPPING.keys())


@bp.route("/task/<string:task_id>/<string:action>", methods=["GET", "POST"])
@project_required
def suspend_task(project: Project, task_id: str, action: str):
    task = Task.query.filter(
        and_(Task.task_id == task_id, Task.project_id == project.id)
    ).first()
    if action in ("suspend", "delete", "activate"):
        getattr(task, action)()
    elif action == "results":
        return render_template("lambdas/task_results.html", task=task)
    return redirect(url_for("tasks.tasks"))
