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

from flask import Blueprint, render_template, request

from galloper.database.models.project import Project
from galloper.database.models.task import Task
from galloper.utils.auth import project_required
from galloper.dal.rabbitmq import get_project_queues

bp = Blueprint("planner", __name__)


@bp.route("/tests", methods=["GET"])
@project_required
def tasks(project: Project):
    tasks_ = Task.query.filter(Task.project_id == project.id).order_by(Task.id).all()
    if request.args.get("type") and request.args.get("type") == "sast":
        return render_template("planner/tests_sast.html", tasks=tasks_, project_id=project.id)
    if request.args.get("type") and request.args.get("type") == "dast":
        return render_template("planner/tests_dast.html", tasks=tasks_, project_id=project.id)
    if request.args.get("type") and request.args.get("type") == "frontend":
        return render_template("planner/frontend_tests.html", tasks=tasks_, project_id=project.id)
    return render_template("planner/tests.html", tasks=tasks_, project_id=project.id)


@bp.route("/tests/backend", methods=["GET", "POST"])
@project_required
def backend(project: Project):
    queues = get_project_queues(project.id)
    if request.args.get("test"):
        return render_template("planner/backend.html", title="Edit performance tests", test_id=request.args.get("test"),
                               project_queues=queues["project"], cloud_queues=queues["clouds"])
    return render_template("planner/backend.html", title="Add performance tests", test_id="null",
                           project_queues=queues["project"], cloud_queues=queues["clouds"])


@bp.route("/tests/frontend", methods=["GET", "POST"])
@project_required
def frontend(project: Project):
    if request.args.get("test"):
        return render_template("planner/frontend.html", title="Edit performance tests", test_id=request.args.get("test"))
    return render_template("planner/frontend.html", title="Add performance tests", test_id="null")


@bp.route("/tests/dast", methods=["GET", "POST"])
@project_required
def dast(project: Project):
    if request.args.get("test"):
        return render_template("planner/dast.html", title="Edit security tests", test_id=request.args.get("test"))
    return render_template("planner/dast.html", title="Add security tests", test_id="null")


@bp.route("/tests/sast", methods=["GET", "POST"])
@project_required
def sast(project: Project):
    if request.args.get("test"):
        return render_template("planner/sast.html", title="Edit security tests", test_id=request.args.get("test"))
    return render_template("planner/sast.html", title="Add security tests", test_id="null")
