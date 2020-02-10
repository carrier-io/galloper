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


from datetime import datetime, timezone
from json import dumps
from flask import Blueprint, request, render_template, flash, current_app, redirect, url_for
from galloper.constants import str_to_timestamp
from galloper.models.api_reports import APIReport
from galloper.dal.influx_results import (get_test_details, get_backend_requests, get_backend_users, get_errors,
                                         get_hits_tps, average_responses, get_build_data, get_tps, get_hits,
                                         get_response_codes, get_sampler_types)
from galloper.dal.loki import get_results

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


def comparison_data(timeline, data):
    labels = []
    for _ in timeline:
        labels.append(datetime.strptime(_, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
    chart_data = {
        "labels": labels,
        "datasets": [
        ]
    }
    col = colors(len(data.keys()))
    for record in data:
        color = col.pop()
        dataset = {
            "label": record,
            "fill": False,
            "data": list(data[record][0].values()),
            "yAxisID": data[record][1],
            "borderWidth": 2,
            "lineTension": 0,
            "spanGaps": True,
            "backgroundColor": f"rgb({color[0]}, {color[1]}, {color[2]})",
            "borderColor": f"rgb({color[0]}, {color[1]}, {color[2]})"
        }
        chart_data["datasets"].append(dataset)
    return dumps(chart_data)


def chart_data(timeline, users, other, yAxis="response_time", dump=True):
    labels = []
    try:
        for _ in timeline:
            labels.append(datetime.strptime(_, "%Y-%m-%dT%H:%M:%SZ").strftime("%m-%d %H:%M:%S"))
    except:
        labels = timeline
    _data = {
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
            "yAxisID": yAxis,
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
        _data['datasets'].append(dataset)
    if dump:
        return dumps(_data)
    else:
        return _data


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


def calculate_proper_timeframe(low_value, high_value, start_time, end_time, aggregation, time_as_ts=False):
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
    if aggregation == 'auto':
        aggregation = f'{seconds}s'
    if time_as_ts:
        return int(start_time), int(end_time), aggregation
    return datetime.fromtimestamp(start_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), \
           datetime.fromtimestamp(end_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), aggregation


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
        samplers = get_sampler_types(test_data['build_id'], test_data['name'], test_data['lg_type'])
        return render_template('perftemplate/api_test_report.html', test_data=test_data,
                               analytics_control=analytics_control, samplers=samplers)


@bp.route('/report/requests/summary', methods=["GET"])
def requests_summary():
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'],
                                                                   request.args.get('aggregator', 'auto'))

    timeline, results, users = get_backend_requests(request.args['build_id'], request.args['test_name'],
                                                    request.args['lg_type'], start_time, end_time, aggregation,
                                                    request.args['sampler'])
    return chart_data(timeline, users, results)


@bp.route('/report/requests/hits', methods=["GET"])
def requests_hits():
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'],
                                                                   request.args.get('aggregator', 'auto'))
    timeline, results, users = get_hits_tps(request.args['build_id'], request.args['test_name'],
                                            request.args['lg_type'], start_time, end_time, aggregation,
                                            request.args['sampler'])
    return chart_data(timeline, users, results)


@bp.route('/report/requests/average', methods=["GET"])
def avg_responses():
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'],
                                                                   request.args.get('aggregator', 'auto'))
    timeline, results, users = average_responses(request.args['build_id'], request.args['test_name'],
                                                 request.args['lg_type'], start_time, end_time, aggregation,
                                                 request.args['sampler'])
    return chart_data(timeline, users, results)


@bp.route("/report/request/table", methods=["GET"])
def summary_table():
    start_time, end_time, _ = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                         request.args.get('high_value', 100),
                                                         request.args['start_time'],
                                                         request.args['end_time'],
                                                         request.args.get('aggregator', 'auto'))
    return dumps(get_build_data(request.args['build_id'], request.args['test_name'],
                                request.args['lg_type'], start_time, end_time,
                                request.args['sampler']))


def calculate_analytics_dataset(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                scope, metric):
    data = None
    axe = 'count'
    if metric == "Throughput":
        timestamps, data, _ = get_tps(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                      scope=scope)
        data = data['responses']
    elif metric == "Hits":
        timestamps, data, _ = get_hits(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                       scope=scope)
        data = data['hits']
    elif metric == "Errors":
        timestamps, data, _ = get_errors(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                         scope=scope)
        data = data['errors']
    elif metric in ["Min", "Median", "Max", "pct90", "pct95", "pct99"]:
        timestamps, data, _ = get_backend_requests(build_id, test_name, lg_type, start_time, end_time, aggregation,
                                                   sampler, scope=scope, aggr=metric)
        data = data['response']
        axe = 'time'

    elif "xx" in metric:
        timestamps, data, _ = get_response_codes(build_id, test_name, lg_type, start_time, end_time, aggregation,
                                                 sampler, scope=scope, aggr=metric)
        data = data['rcodes']
    return data, axe


@bp.route("/report/request/data", methods=["GET"])
def get_data_from_influx():
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'],
                                                                   request.args.get('aggregator', 'auto'))
    metric = request.args.get('metric', '')
    scope = request.args.get('scope', '')
    timestamps, users = get_backend_users(request.args['build_id'], request.args['lg_type'],
                                          start_time, end_time, aggregation)
    axe = 'count'
    if metric == "Users":
        return create_dataset(timestamps, users['users'], f"{scope}_{metric}", axe)
    data, axe = calculate_analytics_dataset(request.args['build_id'], request.args['test_name'],
                                            request.args['lg_type'], start_time, end_time,
                                            aggregation, request.args['sampler'], scope, metric)
    if data:
        return create_dataset(timestamps, data, f"{scope}_{metric}", axe)
    else:
        return {}


@bp.route("/report/all", methods=["GET"])
def get_reports():
    reports = []
    for each in APIReport.query.order_by(APIReport.id.asc()).all():
        each_json = each.to_json()
        each_json['start_time'] = each_json['start_time'].replace("T", " ").split(".")[0]
        each_json['duration'] = int(each_json['duration'])
        each_json['failure_rate'] = round((each_json['failures']/each_json['total'])*100, 2)
        reports.append(each_json)
    return dumps(reports)


@bp.route("/report/compare", methods=["GET"])
def compare_reports():
    samplers = set()
    tests = request.args.getlist('id[]')
    for each in APIReport.query.filter(APIReport.id.in_(tests)).order_by(APIReport.id.asc()).all():
        samplers.update(get_sampler_types(each.build_id, each.name, each.lg_type))
    return render_template('perftemplate/comparison_report.html', samplers=samplers)


@bp.route("/report/compare/data", methods=["GET"])
def prepare_comparison_responses():
    tests = request.args.getlist('id[]')
    tests_meta = []
    longest_test = 0
    longest_time = 0
    sampler = request.args.get('sampler', "REQUEST")
    for i in range(len(tests)):
        data = APIReport.query.filter_by(id=tests[i]).first().to_json()
        if data['duration'] > longest_time:
            longest_time = data['duration']
            longest_test = i
        tests_meta.append(data)
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   tests_meta[longest_test]['start_time'],
                                                                   tests_meta[longest_test]['end_time'],
                                                                   request.args.get('aggregator', 'auto'))
    if request.args.get('aggregator', 'auto') != "auto":
        aggregation = request.args.get('aggregator')
    metric = request.args.get('metric', '')
    scope = request.args.get('scope', '')
    timestamps, users = get_backend_users(tests_meta[longest_test]['build_id'], tests_meta[longest_test]['lg_type'],
                                          start_time, end_time, aggregation)
    test_start_time = "{}_{}".format(tests_meta[longest_test]['start_time'].replace("T", " ").split(".")[0], metric)
    data = {test_start_time: calculate_analytics_dataset(tests_meta[longest_test]['build_id'],
                                                         tests_meta[longest_test]['name'],
                                                         tests_meta[longest_test]['lg_type'],
                                                         start_time, end_time, aggregation,
                                                         sampler, scope, metric)}
    for i in range(len(tests_meta)):
        if i != longest_test:
            test_start_time = "{}_{}".format(tests_meta[i]['start_time'].replace("T", " ").split(".")[0], metric)
            data[test_start_time] = calculate_analytics_dataset(tests_meta[i]['build_id'], tests_meta[i]['name'],
                                                                tests_meta[i]['lg_type'],
                                                                tests_meta[i]['start_time'],
                                                                tests_meta[i]['end_time'],
                                                                aggregation, sampler, scope, metric)
    return comparison_data(timeline=timestamps, data=data)


@bp.route("/report/compare/tests", methods=["GET"])
def compare_tests():
    tests = request.args.getlist('id[]')
    tests_meta = APIReport.query.filter(APIReport.id.in_(tests)).order_by(APIReport.id.asc()).all()
    users_data = {}
    responses_data = {}
    errors_data = {}
    rps_data = {}
    labels = []
    for each in tests_meta:
        ts = datetime.fromtimestamp(str_to_timestamp(each.start_time),
                                    tz=timezone.utc).strftime("%m-%d %H:%M:%S")
        labels.append(ts)
        users_data[ts] = each.vusers
        responses_data[ts] = each.pct95
        errors_data[ts] = each.failures
        rps_data[ts] = each.throughput
    return dumps({
        "response": chart_data(labels, {"users": users_data}, {"pct95": responses_data}, "time", False),
        "errors": chart_data(labels, {"users": users_data}, {"errors": errors_data}, "count", False),
        "rps": chart_data(labels, {"users": users_data}, {"RPS": rps_data}, "count", False)
    })


@bp.route("/report", methods=["GET"])
def report():
    return render_template('perftemplate/report.html')


@bp.route("/report/request/issues")
def get_issues():
    start_time, end_time, aggregation = calculate_proper_timeframe(request.args.get('low_value', 0),
                                                                   request.args.get('high_value', 100),
                                                                   request.args['start_time'],
                                                                   request.args['end_time'],
                                                                   request.args.get('aggregator', 'auto'),
                                                                   time_as_ts=True)
    test_name = request.args['test_name']
    return dumps(list(get_results(test_name, start_time, end_time).values()))

