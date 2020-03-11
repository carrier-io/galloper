#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from flask import Blueprint, render_template
from galloper.models.api_reports import APIReport
from flask_restful import Api, Resource, reqparse
from galloper.dal.influx_results import get_threholds, create_thresholds, delete_threshold

bp = Blueprint('thresholds', __name__)
api = Api(bp)


@bp.route("/thresholds/api", methods=["GET"])
def report():
    tests = APIReport.query.with_entities(APIReport.name).distinct()
    return render_template('quality_gates/thresholds.html', tests=[each[0] for each in tests])


class ApiThresholds(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('name', type=str, location='args')

    delete_parser = reqparse.RequestParser()
    delete_parser.add_argument('test', type=str, location=['args', 'json'])
    delete_parser.add_argument('scope', type=str, location=['args', 'json'])
    delete_parser.add_argument('target', type=str, location=['args', 'json'])
    delete_parser.add_argument('aggregation', type=str, location=['args', 'json'])
    delete_parser.add_argument('comparison', type=str, location=['args', 'json'])

    post_parser = delete_parser.copy()
    post_parser.add_argument('yellow', type=float, location='json')
    post_parser.add_argument('red', type=float, location='json')

    def get(self):
        args = self.get_parser.parse_args(strict=False)
        return get_threholds(args.get("name"))

    def post(self):
        args = self.post_parser.parse_args(strict=False)
        create_thresholds(args['test'], args['scope'], args['target'], args['aggregation'],
                          args['comparison'], args['yellow'], args['red'])
        return {"message": "OK"}

    def delete(self):
        args = self.delete_parser.parse_args(strict=False)
        delete_threshold(args['test'], args['target'], args['scope'],
                         args['aggregation'], args['comparison'])
        return {"message": "OK"}


class ApiRequests(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('name', type=str, location='args')

    def get(self):
        args = self.get_parser.parse_args(strict=False)
        requests_data = set()
        for each in APIReport.query.filter(APIReport.name == args.get('name')).order_by(APIReport.id.asc()).all():
            requests_data.update(set(each.requests.split(";")))
        return list(requests_data)


api.add_resource(ApiThresholds, "/api/thresholds")
api.add_resource(ApiRequests, "/api/requests")
