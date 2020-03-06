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

from flask import Blueprint, render_template

from galloper.database.models.api_reports import APIReport
from galloper.database.models.project import Project

bp = Blueprint("thresholds", __name__)


@bp.route("/<int:project_id>/thresholds", methods=["GET"])
def report(project_id: int):
    project = Project.get_object_or_404(pk=project_id)
    tests = APIReport.query.filter(APIReport.project_id == project.id).with_entities(APIReport.name).all()
    return render_template("quality_gates/thresholds.html", tests=[each[0] for each in tests])
