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
from galloper.data_utils.charts_utils import get_throughput_per_test, get_response_time_per_test
from galloper.data_utils import arrays


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
        project = Project.query.get_or_404(project_id)
        return [
            each.to_json() for each in APIRelease.query.filter_by(project_id=project.id)
        ]

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.query.get_or_404(project_id)
        release = APIRelease(
            project_id=project.id,
            release_date=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            release_name=args["release_name"]
        )
        release.insert()
        return release.to_json()

    def put(self, project_id: int):
        args = self._parser_put.parse_args(strict=False)
        project = Project.query.get_or_404(project_id)
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
        project = Project.query.get_or_404(project_id)
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


class ReleaseApiSaturation(Resource):
    _rules = (
        dict(name="release_name", type=str, location="args"),
        dict(name="release_id", type=int, location="args"),
        dict(name='sampler', type=str, location="args", required=True),
        dict(name='request', type=str, location="args", required=True),
        dict(name='test_name', type=str, location="args", required=True),
        dict(name='environment', type=str, location="args", required=True),
        dict(name='max_errors', type=float, default=1.0, location="args"),
        dict(name='aggregation', type=str, default="1s", location="args"),
        dict(name='global', type=str, default=None, location="args"),
        dict(name='status', type=str, default='ok', location="args")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser = build_req_parser(rules=self._rules)

    def get(self, project_id: int):
        args = self._parser.parse_args(strict=False)
        response_time = []
        throughput = []
        error_rate = []
        global_error_rate = []
        users = []
        project = Project.query.get_or_404(project_id)
        try:
            if args.get("release_name"):
                release_id = APIRelease.query.filter(
                    and_(APIRelease.project_id == project.id,
                         APIRelease.release_name == args.get("release_name"))
                ).first().id
            else:
                release_id = args.get("release_id")
            api_reports = APIReport.query.filter(and_(
                APIRelease.project_id == project.id,
                APIReport.release_id == release_id,
                APIReport.name == args["test_name"],
                APIReport.environment == args["environment"])).order_by(APIReport.vusers.asc()).all()
            for _ in api_reports:
                users.append(_.vusers)
                if args["global"]:
                    errors_count = int(get_response_time_per_test(_.build_id, _.name, _.lg_type, None,
                                                                  'All', "errors"))
                    total = int(get_response_time_per_test(_.build_id, _.name, _.lg_type, None,
                                                           'All', "total"))
                    global_error_rate.append(round(float(errors_count / total) * 100, 2))
                throughput.append(get_throughput_per_test(
                    _.build_id, _.name, _.lg_type, args["sampler"], args["request"], args["aggregation"], args["status"]))
                response_time.append(get_response_time_per_test(
                    _.build_id, _.name, _.lg_type, args["sampler"], args["request"], "pct95", args["status"]))
                error_rate.append(get_response_time_per_test(
                    _.build_id, _.name, _.lg_type, args["sampler"], args["request"], "errors"))
            if arrays.non_decreasing(throughput):
                return {"message": "proceed", "users": users, "error_rate": int(global_error_rate[-1]), "code": 0}
            else:
                return {
                    "message": "saturation",
                    "users": users,
                    "throughput": throughput,
                    "errors": error_rate,
                    "code": 1
                }
        except (AttributeError, IndexError):
            return {
                "message": "exception",
                "error_rate": error_rate,
                "users": users,
                "global_errors": global_error_rate,
                "code": 1
            }
