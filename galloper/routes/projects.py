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


from galloper.database.models.project import Project
from galloper.utils.auth import SessionProject

bp = Blueprint("projects", __name__)


@bp.route("/projects", methods=["GET"])
def projects():
    return render_template("projects/projects.html")


@bp.route("/project/add", methods=["GET", "POST"])
def add_project():
    if request.method == "POST":
        project = Project(name=request.form["name"])
        project.insert()
        SessionProject.set(project.id)
        return redirect(url_for("projects.projects"))

    return render_template("projects/add_project.html")


@bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("projects.projects"))
