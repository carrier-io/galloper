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
from galloper.utils.auth import project_required, superadmin_required, filter_projects, is_superadmin

bp = Blueprint("projects", __name__)


@bp.route("/projects", methods=["GET"])
def list():
    return render_template("projects/projects.html", is_superadmin=is_superadmin())


@bp.route("/projects/health", methods=["GET"])
@filter_projects
def project_health(project_list: list):
    return render_template("projects/projects_health.html")


@bp.route("/project/add", methods=["GET", "POST"])
@superadmin_required
def add():
    return render_template("projects/add_project.html")


@bp.route("/project/configure", methods=["GET", "POST"])
@project_required
def configure(project: Project):
    return render_template("projects/configure.html", project=project, is_superadmin=is_superadmin())


@bp.route("/token", methods=["GET"])
def display_token():
    return render_template("projects/token.html", id=request.args.get("id", "Nothing"))


@bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("projects.list"))
