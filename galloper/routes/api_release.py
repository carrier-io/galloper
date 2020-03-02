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
from flask import Blueprint
from flask_restful import Api, Resource, reqparse

from galloper.database.models.api_release import APIRelease
from galloper.database.models.api_reports import APIReport

bp = Blueprint('releases_api', __name__)
api = Api(bp)

port_parser = reqparse.RequestParser()
port_parser.add_argument("release_name", type=str, location="json")

put_parser = reqparse.RequestParser()
put_parser.add_argument("release_id", type=int, location="json")
put_parser.add_argument("reports", type=list, location="json")


class ReleaseApi(Resource):
    def get(self):
        return [each.to_json() for each in APIRelease.query.all()]

    def post(self):
        args = port_parser.parse_args(strict=False)
        release = APIRelease(release_date=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                             release_name=args['release_name'])
        release.insert()
        return release.to_json()

    def put(self):
        args = put_parser.parse_args(strict=False)
        updated_reports = []
        for _ in args['reports']:
            report = APIReport.query.filter_by(id=_).first()
            report.release_id = args["release_id"]
            report.commit()
            updated_reports.append(report.to_json())
        return {"message": updated_reports}


class ReleaseApiReports(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("release_name", type=str, location="args")
    parser.add_argument("release_id", type=int, location="args")

    def get(self):
        args = self.parser.parse_args(strict=False)
        try:
            if args.get("release_name"):
                release_id = APIRelease.query.filter_by(release_name=args.get("release_name")).first().id
            else:
                release_id = args.get("release_id")
            api_reports = [each.id for each in APIReport.query.filter_by(release_id=release_id).all()]
            return api_reports
        except AttributeError:
            return []


api.add_resource(ReleaseApi, "/api/releases/api")
api.add_resource(ReleaseApiReports, "/api/releases/api/reports")
