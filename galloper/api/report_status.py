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


from flask_restful import Resource
from galloper.utils.api_utils import build_req_parser
from galloper.database.models.api_reports import APIReport
from galloper.database.models.security_reports import SecurityReport
from galloper.database.models.ui_report import UIReport
from galloper.database.models.project import Project


REPORTS_MAPPER = {
    "backend": APIReport,
    "frontend": UIReport,
    "security": SecurityReport
}


class ReportStatusAPI(Resource):
    put_rules = (
        dict(name="status", type=str, location="json"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_put = build_req_parser(rules=self.put_rules)

    def get(self, project_id: int, report_type: str, report_id: int):
        project = Project.get_or_404(project_id)
        report = REPORTS_MAPPER.get(report_type).query.filter_by(project_id=project.id, id=report_id).first().to_json()
        return {"message": report["status"]}

    def put(self, project_id: int, report_type: str, report_id: int):
        args = self._parser_put.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        report = REPORTS_MAPPER.get(report_type).query.filter_by(project_id=project.id, id=report_id).first()
        report.status = args["status"]
        report.commit()
        return {"message": f"status changed to {args['status']}"}
