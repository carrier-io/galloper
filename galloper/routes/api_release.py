from datetime import datetime
from flask import Blueprint, request, render_template
from flask_restful import Api, Resource, reqparse
from galloper.models.api_reports import APIReport
from galloper.models.api_release import APIRelease


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


api.add_resource(ReleaseApi, "/api/releases/api")
