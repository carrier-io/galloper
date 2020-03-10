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

from datetime import datetime

from flask_restful import Resource
from sqlalchemy import and_

from galloper.database.models.api_release import APIRelease
from galloper.database.models.api_reports import APIReport
from galloper.database.models.project import Project
from galloper.utils.api_utils import build_req_parser


class ReleaseAPI(Resource):
    post_rules = (
        dict(name="release_name", type=str, location="json"),
    )
    put_rules = (
        dict(name="release_id", type=int, location="json"),
        dict(name="reports", type=list, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_put = build_req_parser(rules=self.put_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int):
        project = Project.get_object_or_404(pk=project_id)
        return [
            each.to_json() for each in APIRelease.query.filter_by(project_id=project.id)
        ]

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        release = APIRelease(
            project_id=project.id,
            release_date=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            release_name=args["release_name"]
        )
        release.insert()
        return release.to_json()

    def put(self, project_id: int):
        args = self._parser_put.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        updated_reports = []

        query_params = and_(APIReport.id.in_(args["reports"]), APIReport.project_id == project.id)

        for report in APIReport.query.filter(query_params).all():
            report.release_id = args["release_id"]
            report.commit()
            updated_reports.append(report.to_json())
        return {"message": updated_reports}


class ApiReportsAPI(Resource):
    get_rules = (
        dict(name="release_name", type=str, location="args"),
        dict(name="release_id", type=int, location="args")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        try:
            if args.get("release_name"):
                release_id = APIRelease.query.filter(
                    and_(APIRelease.release_name == args.get("release_name"), APIReport.project_id == project.id)
                ).first().id
            else:
                release_id = args.get("release_id")
            api_reports = APIReport.query.filter(
                and_(APIReport.release_id == release_id, APIReport.project_id == project.id)
            ).all()
            api_report_ids = [each.id for each in api_reports]
            return api_report_ids
        except AttributeError:
            return []
