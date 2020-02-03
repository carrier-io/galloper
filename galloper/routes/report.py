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

import os
from copy import deepcopy
from datetime import datetime, timezone
from json import dumps
from flask import Blueprint, request, render_template, flash, current_app, redirect, url_for
from galloper.constants import str_to_timestamp
from galloper.models.api_reports import APIReport
from galloper.dal.influx_results import (get_test_details, get_backend_requests, get_backend_users, get_errors,
                                         get_hits_tps, average_responses, get_build_data, get_tps, get_hits,
                                         get_response_codes)

bp = Blueprint('reports', __name__)

import random

MAX_DOTS_ON_CHART = 100

def colors(n):
    try:
        ret = []
        r = int(random.random() * 256)
        g = int(random.random() * 256)
        b = int(random.random() * 256)
        step = 256 / n
        for i in range(n):
            r += step
            g += step
            b += step
            r = int(r) % 256
            g = int(g) % 256
            b = int(b) % 256
            ret.append((r, g, b))
        return ret
    except ZeroDivisionError:
        return [(0, 0, 0)]


def create_dataset(timeline, data, label, axe):
    labels = []
    for _ in timeline:
        labels.append(datetime.strptime(_, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
    color = colors(1)[0]
    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": label,
                "fill": False,
                "data": list(data.values()),
                "yAxisID": axe,
                "borderWidth": 2,
                "lineTension": 0,
                "spanGaps": True,
                "backgroundColor": f"rgb({color[0]}, {color[1]}, {color[2]})",
                "borderColor": f"rgb({color[0]}, {color[1]}, {color[2]})"
            }
        ]
    }
    return dumps(chart_data)


def chart_data(timeline, users, other):
    labels = []
    for _ in timeline:
        labels.append(datetime.strptime(_, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": "Active Users",
                "fill": False,
                "data": list(users['users'].values()),
                "yAxisID": "active_users",
                "borderWidth": 2,
                "lineTension": 0,
                "spanGaps": True
            }
        ]
    }
    colors_array = colors(len(other.keys()))
    for each in other:
        color = colors_array.pop()
        dataset = {
            "label": each,
            "fill": False,
            "backgroundColor": f"rgb({color[0]}, {color[1]}, {color[2]})",
            "yAxisID": "response_time",
            "borderWidth": 1,
            "lineTension": 0.2,
            "pointRadius": 1,
            "spanGaps": True,
            "borderColor": f"rgb({color[0]}, {color[1]}, {color[2]})",
            "data": []
        }
        for _ in timeline:
            if _ in other[each]:
                dataset['data'].append(other[each][_])
            else:
                dataset['data'].append(None)
        chart_data['datasets'].append(dataset)
    return dumps(chart_data)


def render_analytics_control(requests):
    item = {
        "Users": "getData('Users', '{}')",
        "Hits": "getData('Hits', '{}')",
        "Throughput": "getData('Throughput', '{}')",
        "Errors": "getData('Errors', '{}')",
        "Min": "getData('Min', '{}')",
        "Median": "getData('Median', '{}')",
        "Max": "getData('Max', '{}')",
        "pct90": "getData('pct90', '{}')",
        "pct95": "getData('pct95', '{}')",
        "pct99": "getData('pct99', '{}')",
        "1xx": "getData('1xx', '{}')",
        "2xx": "getData('2xx', '{}')",
        "3xx": "getData('3xx', '{}')",
        "4xx": "getData('4xx', '{}')",
        "5xx": "getData('5xx', '{}')"
    }
    control = {}
    for each in ["All"] + requests:
        control[each] = {}
        for every in item:
            control[each][every] = item[every].format(each)
    return control


def calculate_proper_timeframe(low_value, high_value, start_time, end_time):
    start_time = str_to_timestamp(start_time)
    end_time = str_to_timestamp(end_time)
    interval = end_time-start_time
    start_shift = interval*(float(low_value)/100.0)
    end_shift = interval*(float(high_value)/100.0)
    end_time = start_time + end_shift
    start_time += start_shift
    real_interval = end_time - start_time
    seconds = real_interval/MAX_DOTS_ON_CHART
    if seconds > 1:
        seconds = int(seconds)
    else:
        seconds = 1
    return datetime.fromtimestamp(start_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), \
           datetime.fromtimestamp(end_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), f'{seconds}s'


@bp.route("/report/create", methods=["GET", "POST"])
def add_report():
    test_data = get_test_details(build_id=request.args['build_id'], test_name=request.args['test_name'],
                                 lg_type=request.args['lg_type'])

    report = APIReport(name=test_data['name'], environment=test_data["environment"], type=test_data["type"],
                       end_time=test_data["end_time"], start_time=test_data["start_time"],
                       failures=test_data["failures"], total=test_data["total"],
                       thresholds_missed=request.args.get("missed", 0), throughput=test_data["throughput"],
                       vusers=test_data["vusers"], pct95=test_data["pct95"], duration=test_data["duration"],
                       build_id=request.args['build_id'], lg_type=request.args['lg_type'],
                       onexx=test_data["1xx"], twoxx=test_data["2xx"], threexx=test_data["3xx"],
                       fourxx=test_data["4xx"], fivexx=test_data["5xx"],
                       requests=";".join(test_data["requests"]))
    report.insert()
    return "OK", 201


@bp.route('/report/backend', methods=["GET", "POST"])
def view_report():
    if request.method == 'GET':
        if request.args.get("report_id", None):
            test_data = APIReport.query.filter_by(id=request.args.get("report_id")).first().to_json()
        else:
            test_data = get_test_details(build_id=request.args['build_id'], test_name=request.args['test_name'],
                                         lg_type=request.args['lg_type'])
        analytics_control = render_analytics_control(test_data['requests'])
        return render_template('perftemplate/api_test_report.html', test_data=test_data,
                               analytics_control=analytics_control)


@bp.route('/report/requests/summary', methods=["GET"])
def requests_summary():
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'])
    timeline, results, users = get_backend_requests(request.args['build_id'], request.args['test_name'],
                                                    request.args['lg_type'], start_time, end_time, aggregation)
    return chart_data(timeline, users, results)


@bp.route('/report/requests/hits', methods=["GET"])
def requests_hits():
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'])
    timeline, results, users = get_hits_tps(request.args['build_id'], request.args['test_name'],
                                            request.args['lg_type'], start_time, end_time, aggregation)
    return chart_data(timeline, users, results)


@bp.route('/report/requests/average', methods=["GET"])
def avg_responses():
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'])
    timeline, results, users = average_responses(request.args['build_id'], request.args['test_name'],
                                                 request.args['lg_type'], start_time, end_time, aggregation)
    return chart_data(timeline, users, results)


@bp.route("/report/request/table", methods=["GET"])
def summary_table():
    start_time, end_time, _ = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                         request.args.get('high_value', 100),
                                                         request.args['start_time'],
                                                         request.args['end_time'])
    return dumps(get_build_data(request.args['build_id'], request.args['test_name'],
                                request.args['lg_type'], start_time, end_time))


@bp.route("/report/request/data", methods=["GET"])
def get_data_from_influx():
    data = None
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'])
    metric = request.args.get('metric', '')
    scope = request.args.get('scope', '')
    timestamps, users = get_backend_users(request.args['build_id'], request.args['lg_type'],
                                          start_time, end_time, aggregation)
    axe = 'count'
    if metric == "Users":
        return create_dataset(timestamps, users['users'], f"{scope}_{metric}", axe)
    elif metric == "Throughput":
        timestamps, data, _ = get_tps(request.args['build_id'], request.args['test_name'],
                                      request.args['lg_type'], start_time, end_time, aggregation, scope=scope)
        data = data['responses']
    elif metric == "Hits":
        timestamps, data, _ = get_hits(request.args['build_id'], request.args['test_name'],
                                       request.args['lg_type'], start_time, end_time, aggregation, scope=scope)
        data = data['hits']
    elif metric == "Errors":
        timestamps, data, _ = get_errors(request.args['build_id'], request.args['test_name'],
                                         request.args['lg_type'], start_time, end_time, aggregation, scope=scope)
        data = data['errors']
    elif metric in ["Min", "Median", "Max", "pct90", "pct95", "pct99"]:
        timestamps, data, _ = get_backend_requests(request.args['build_id'], request.args['test_name'],
                                                   request.args['lg_type'], start_time, end_time, aggregation,
                                                   scope=scope, aggr=metric)
        data = data['response']
        axe = 'time'

    elif "xx" in metric:
        timestamps, data, _ = get_response_codes(request.args['build_id'], request.args['test_name'],
                                                 request.args['lg_type'], start_time, end_time, aggregation,
                                                 scope=scope, aggr=metric)
        data = data['rcodes']
    if data:
        return create_dataset(timestamps, data, f"{scope}_{metric}", axe)
    else:
        return {}


