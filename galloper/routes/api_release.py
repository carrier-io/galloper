from datetime import datetime
from flask import Blueprint
from flask_restful import Api, Resource, reqparse
from sqlalchemy import and_
from galloper.models.api_reports import APIReport
from galloper.models.api_release import APIRelease
from galloper.data_utils.charts_utils import get_throughput_per_test, get_response_time_per_test
from galloper.data_utils import arrays

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


class ReleaseApiSaturation(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("release_name", type=str, location="args")
    parser.add_argument("release_id", type=int, location="args")
    parser.add_argument('sampler', type=str, location="args", required=True)
    parser.add_argument('request', type=str, location="args", required=True)
    parser.add_argument('test_name', type=str, location="args", required=True)
    parser.add_argument('environment', type=str, location="args", required=True)
    parser.add_argument('max_errors', type=float, default=1.0, location="args")
    parser.add_argument('aggregation', type=str, default="1s", location="args")

    def get(self):
        args = self.parser.parse_args(strict=False)
        try:
            if args.get("release_name"):
                release_id = APIRelease.query.filter_by(release_name=args.get("release_name")).first().id
            else:
                release_id = args.get("release_id")
            api_reports = APIReport.query.filter(and_(
                APIReport.release_id == release_id,
                APIReport.name == args["test_name"],
                APIReport.environment == args["environment"])).order_by(APIReport.vusers.asc()).all()
            response_time = []
            throughput = []
            error_rate = []
            users = []
            for _ in api_reports:
                users.append(_.vusers)
                throughput.append(
                    get_throughput_per_test(_.build_id, _.name, _.lg_type, args["sampler"], args["request"],
                                            args["aggregation"]))
                response_time.append(get_response_time_per_test(_.build_id, _.name, _.lg_type, args["sampler"],
                                                                args["request"], "pct95"))
                errors_count = int(get_response_time_per_test(_.build_id, _.name, _.lg_type, args["sampler"],
                                                              args["request"], "errors"))
                total = int(get_response_time_per_test(_.build_id, _.name, _.lg_type, args["sampler"],
                                                       args["request"], "total"))
                error_rate.append(round(float(errors_count/total) * 100, 2))
            if arrays.non_decreasing(throughput) and arrays.within_bounds(error_rate, args['max_errors']):
                return {"message": "proceed", "code": 0}
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
                "code": 1
            }


api.add_resource(ReleaseApi, "/api/releases/api")
api.add_resource(ReleaseApiReports, "/api/releases/api/reports")
api.add_resource(ReleaseApiSaturation, "/api/releases/saturation")
