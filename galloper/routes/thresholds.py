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
from flask_restful import Api, Resource, reqparse
from sqlalchemy import and_

from galloper.dal.influx_results import get_threholds, create_thresholds, delete_threshold
from galloper.database.models.api_reports import APIReport
from galloper.database.models.project import Project

bp = Blueprint("thresholds", __name__)
api = Api(bp)


@bp.route("/<int:project_id>/thresholds/api", methods=["GET"])
def report(project_id):
    project = Project.get_object_or_404(pk=project_id)
    tests = APIReport.query.filter(APIReport.project_id == project.id).with_entities(APIReport.name).all()
    return render_template("quality_gates/thresholds.html", tests=[each[0] for each in tests])


class ApiThresholds(Resource):
    _get_parser = reqparse.RequestParser()
    _get_parser.add_argument("name", type=str, location="args")

    _delete_parser = reqparse.RequestParser()
    _delete_parser.add_argument("test", type=str, location=["args", "json"])
    _delete_parser.add_argument("scope", type=str, location=["args", "json"])
    _delete_parser.add_argument("target", type=str, location=["args", "json"])
    _delete_parser.add_argument("aggregation", type=str, location=["args", "json"])
    _delete_parser.add_argument("comparison", type=str, location=["args", "json"])

    _post_parser = _delete_parser.copy()
    _post_parser.add_argument("yellow", type=float, location="json")
    _post_parser.add_argument("red", type=float, location="json")

    def get(self):
        args = self.get_parser.parse_args(strict=False)
        return get_threholds(test_name=args.get("name"))

    def post(self):
        args = self._post_parser.parse_args(strict=False)
        create_thresholds(
            test=args["test"],
            scope=args["scope"],
            target=args["target"],
            aggregation=args["aggregation"],
            comparison=args["comparison"],
            yellow=args["yellow"],
            red=args["red"]
        )
        return {"message": "OK"}

    def delete(self):
        args = self._delete_parser.parse_args(strict=False)
        delete_threshold(
            test=args["test"],
            target=args["target"],
            scope=args["scope"],
            aggregation=args["aggregation"],
            comparison=args["comparison"]
        )
        return {"message": "OK"}


class ApiRequests(Resource):
    _get_parser = reqparse.RequestParser()
    _get_parser.add_argument("name", type=str, location="args")

    def get(self, project_id: int):
        args = self._get_parser.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)

        requests_data = set()
        query_result = APIReport.query.filter(
            and_(APIReport.name == args.get("name"), APIReport.project_id == project.id)
        ).order_by(APIReport.id.asc()).all()

        for each in query_result:
            requests_data.update(set(each.requests.split(";")))
        return list(requests_data)


api.add_resource(ApiThresholds, "/api/thresholds")
api.add_resource(ApiRequests, "/api/<int:project_id>/requests")

