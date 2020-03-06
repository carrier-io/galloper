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

from flask import Blueprint, request, render_template

from galloper.dal.influx_results import get_test_details, get_sampler_types
from galloper.data_utils.report_utils import render_analytics_control
from galloper.database.models.api_reports import APIReport
from galloper.database.models.security_results import SecurityResults

bp = Blueprint("reports", __name__)


@bp.route("/report", methods=["GET"])
def report():
    return render_template("perftemplate/report.html")


@bp.route("/security", methods=["GET"])
def security():
    return render_template("security/report.html")


@bp.route("/security/finding", methods=["GET"])
def findings():
    report_id = request.args.get("id", None)
    test_data = SecurityResults.query.filter_by(id=report_id).first()
    return render_template("security/results.html", test_data=test_data)


@bp.route("/report/backend", methods=["GET", "POST"])
def view_report():
    if request.method == "GET":
        if request.args.get("report_id", None):
            test_data = APIReport.query.filter_by(id=request.args.get("report_id")).first().to_json()
        else:
            test_data = get_test_details(build_id=request.args["build_id"],
                                         test_name=request.args["test_name"],
                                         lg_type=request.args["lg_type"])
        analytics_control = render_analytics_control(test_data["requests"])
        samplers = get_sampler_types(test_data["build_id"], test_data["name"], test_data["lg_type"])
        return render_template("perftemplate/api_test_report.html", test_data=test_data,
                               analytics_control=analytics_control, samplers=samplers)


@bp.route("/report/compare", methods=["GET"])
def compare_reports():
    samplers = set()
    requests_data = set()
    tests = request.args.getlist("id[]")
    for each in APIReport.query.filter(APIReport.id.in_(tests)).order_by(APIReport.id.asc()).all():
        samplers.update(get_sampler_types(each.build_id, each.name, each.lg_type))
        requests_data.update(set(each.requests.split(";")))
    return render_template("perftemplate/comparison_report.html", samplers=samplers, requests=requests_data)
