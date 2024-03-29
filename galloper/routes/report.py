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
from sqlalchemy import and_

from galloper.dal.influx_results import get_test_details, get_sampler_types
from galloper.data_utils.report_utils import render_analytics_control
from galloper.database.models.api_reports import APIReport
from galloper.database.models.security_results import SecurityResults
from galloper.database.models.project import Project
from galloper.database.models.ui_report import UIReport
from galloper.database.models.ui_result import UIResult
from galloper.utils.auth import project_required

bp = Blueprint("reports", __name__)


@bp.route("/report", methods=["GET"])
@project_required
def report(project: Project):
    return render_template("perftemplate/report.html")


@bp.route("/security", methods=["GET"])
@project_required
def security(project: Project):
    report_type = request.args.get("type", None)
    return render_template("security/report.html", report_type=report_type)


@bp.route("/visual", methods=["GET"])
@project_required
def visual(project: Project):
    return render_template("observer/report.html")


@bp.route("/security/finding", methods=["GET"])
@project_required
def findings(project: Project):
    report_id = request.args.get("id", None)
    test_data = SecurityResults.query.filter(
        and_(SecurityResults.project_id == project.id, SecurityResults.id == report_id)).first()
    return render_template("security/results.html", test_data=test_data)


@bp.route("/report/backend", methods=["GET"])
@project_required
def view_report(project: Project):
    if request.args.get("report_id", None):
        test_data = APIReport.query.filter_by(id=request.args.get("report_id")).first().to_json()
    else:
        test_data = get_test_details(project_id=project.id,
                                     build_id=request.args["build_id"],
                                     test_name=request.args["test_name"],
                                     lg_type=request.args["lg_type"])
    analytics_control = render_analytics_control(test_data["requests"])
    samplers = get_sampler_types(project.id, test_data["build_id"], test_data["name"], test_data["lg_type"])
    return render_template("perftemplate/api_test_report.html", test_data=test_data,
                           analytics_control=analytics_control, samplers=samplers)


@bp.route("/report/compare", methods=["GET"])
@project_required
def compare_reports(project: Project):
    samplers = set()
    requests_data = set()
    tests = request.args.getlist("id[]")
    for each in APIReport.query.filter(
        and_(APIReport.id.in_(tests)), APIReport.project_id == project.id
    ).order_by(APIReport.id.asc()).all():
        samplers.update(get_sampler_types(project.id, each.build_id, each.name, each.lg_type))
        requests_data.update(set(each.requests.split(";")))
    return render_template("perftemplate/comparison_report.html", samplers=samplers, requests=requests_data)


@bp.route("/visual/report", methods=["GET"])
@project_required
def visual_report(project: Project):
    # expected report level data
    from uuid import uuid4
    report_id = request.args.getlist("report_id")[0]

    ui_report = UIReport.query.filter_by(id=report_id, project_id=project.id).first_or_404()
    results = UIResult.query.filter_by(report_uid=ui_report.uid).all()

    totals = list(map(lambda x: x.total, results))
    try:
        avg_page_load = sum(totals) / len(totals)
    except ZeroDivisionError:
        avg_page_load = 0
    try:
        thresholds_missed = round(ui_report.thresholds_failed / ui_report.thresholds_total * 100, 2)
    except ZeroDivisionError:
        thresholds_missed = 0

    failures = len(results)
    if not ui_report.passed:
        failures = 0

    try:
        browser_version = results[0].browser_version.split(" ")[1]
    except:
        browser_version = "undefined"
    try:
        resolution = results[0].resolution
    except:
        resolution = 0
    test_data = dict(id=report_id, project_id=project.id, name=ui_report.name,
                     report_id=ui_report.uid,
                     environment=ui_report.environment,
                     browser=ui_report.browser,
                     browser_version=browser_version,
                     resolution=resolution,
                     url=ui_report.base_url,
                     end_time=ui_report.stop_time, start_time=ui_report.start_time,
                     duration=ui_report.duration,
                     failures=failures,
                     total=len(results),
                     aggregation=ui_report.aggregation,
                     thresholds_missed=thresholds_missed,
                     avg_page_load=round(avg_page_load / 1000, 2),
                     avg_step_duration=0, build_id=str(uuid4()), release_id=1)
    return render_template("observer/results.html", test_data=test_data)
