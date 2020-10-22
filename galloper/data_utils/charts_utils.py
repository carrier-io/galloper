from datetime import datetime, timezone
from galloper.database.models.api_reports import APIReport
from galloper.dal.influx_results import (get_backend_requests, get_hits_tps, average_responses, get_build_data, get_tps,
                                         get_hits, get_errors, get_response_codes, get_backend_users,
                                         get_throughput_per_test, get_response_time_per_test)
from galloper.dal.loki import get_results
from galloper.data_utils.report_utils import calculate_proper_timeframe, chart_data, create_dataset, comparison_data
from galloper.constants import str_to_timestamp


def _timeframe(args, time_as_ts=False):
    end_time = args['end_time']
    high_value = args.get('high_value', 100)
    if not end_time:
        end_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        high_value = 100
    return calculate_proper_timeframe(args.get('low_value', 0), high_value,
                                      args['start_time'], end_time, args.get('aggregator', 'auto'),
                                      time_as_ts=time_as_ts)


def _query_only(args, query_func):
    start_time, end_time, aggregation = _timeframe(args)
    timeline, results, users = query_func(args['build_id'], args['test_name'], args['lg_type'],
                                          start_time, end_time, aggregation,
                                          sampler=args['sampler'], status=args["status"])
    return chart_data(timeline, users, results)


def get_tests_metadata(tests):
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
    return labels, rps_data, errors_data, users_data, responses_data


def requests_summary(args):
    return _query_only(args, get_backend_requests)


def requests_hits(args):
    return _query_only(args, get_hits_tps)


def avg_responses(args):
    return _query_only(args, average_responses)


def summary_table(args):
    start_time, end_time, aggregation = _timeframe(args)
    return get_build_data(args['build_id'], args['test_name'], args['lg_type'], start_time, end_time, args['sampler'])


def get_issues(args):
    start_time, end_time, aggregation = _timeframe(args, time_as_ts=True)
    return list(get_results(args['test_name'], start_time, end_time).values())


def calculate_analytics_dataset(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                scope, metric, status):
    data = None
    axe = 'count'
    if metric == "Throughput":
        timestamps, data, _ = get_tps(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                      scope=scope, status=status)
        data = data['responses']
    elif metric == "Hits":
        timestamps, data, _ = get_hits(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                       scope=scope, status=status)
        data = data['hits']
    elif metric == "Errors":
        timestamps, data, _ = get_errors(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                                         scope=scope)
        data = data['errors']
    elif metric in ["Min", "Median", "Max", "pct90", "pct95", "pct99"]:
        timestamps, data, _ = get_backend_requests(build_id, test_name, lg_type, start_time, end_time, aggregation,
                                                   sampler, scope=scope, aggr=metric, status=status)
        data = data['response']
        axe = 'time'

    elif "xx" in metric:
        timestamps, data, _ = get_response_codes(build_id, test_name, lg_type, start_time, end_time, aggregation,
                                                 sampler, scope=scope, aggr=metric, status=status)
        data = data['rcodes']
    return data, axe


def get_data_from_influx(args):
    start_time, end_time, aggregation = _timeframe(args)
    metric = args.get('metric', '')
    scope = args.get('scope', '')
    project_id = APIReport.query.filter_by(build_id=args["build_id"]).first().to_json()["project_id"]
    timestamps, users = get_backend_users(project_id, args['build_id'], args['lg_type'],
                                          start_time, end_time, aggregation)
    axe = 'count'
    if metric == "Users":
        return create_dataset(timestamps, users['users'], f"{scope}_{metric}", axe)
    data, axe = calculate_analytics_dataset(args['build_id'], args['test_name'], args['lg_type'],
                                            start_time, end_time, aggregation, args['sampler'],
                                            scope, metric, args["status"])
    if data:
        return create_dataset(timestamps, data, f"{scope}_{metric}", axe)
    else:
        return {}


def prepare_comparison_responses(args):
    tests = args['id[]']
    tests_meta = []
    longest_test = 0
    longest_time = 0
    sampler = args.get('sampler', "REQUEST")
    for i in range(len(tests)):
        data = APIReport.query.filter_by(id=tests[i]).first().to_json()
        if data['duration'] > longest_time:
            longest_time = data['duration']
            longest_test = i
        tests_meta.append(data)
    start_time, end_time, aggregation = calculate_proper_timeframe(args.get('low_value', 0),
                                                                   args.get('high_value', 100),
                                                                   tests_meta[longest_test]['start_time'],
                                                                   tests_meta[longest_test]['end_time'],
                                                                   args.get('aggregator', 'auto'))
    if args.get('aggregator', 'auto') != "auto":
        aggregation = args.get('aggregator')
    metric = args.get('metric', '')
    scope = args.get('scope', '')
    status = args.get("status", 'all')
    timestamps, users = get_backend_users(project_id, tests_meta[longest_test]['build_id'],
                                          tests_meta[longest_test]['lg_type'], start_time, end_time, aggregation)
    test_start_time = "{}_{}".format(tests_meta[longest_test]['start_time'].replace("T", " ").split(".")[0], metric)
    data = {test_start_time: calculate_analytics_dataset(tests_meta[longest_test]['build_id'],
                                                         tests_meta[longest_test]['name'],
                                                         tests_meta[longest_test]['lg_type'],
                                                         start_time, end_time, aggregation,
                                                         sampler, scope, metric, status)}
    for i in range(len(tests_meta)):
        if i != longest_test:
            test_start_time = "{}_{}".format(tests_meta[i]['start_time'].replace("T", " ").split(".")[0], metric)
            data[test_start_time] = calculate_analytics_dataset(tests_meta[i]['build_id'], tests_meta[i]['name'],
                                                                tests_meta[i]['lg_type'],
                                                                tests_meta[i]['start_time'],
                                                                tests_meta[i]['end_time'],
                                                                aggregation, sampler, scope, metric, status)
    return comparison_data(timeline=timestamps, data=data)


def compare_tests(args):
    labels, rps_data, errors_data, users_data, responses_data = get_tests_metadata(args['id[]'])
    return {
        "response": chart_data(labels, {"users": users_data}, {"pct95": responses_data}, "time"),
        "errors": chart_data(labels, {"users": users_data}, {"errors": errors_data}, "count"),
        "rps": chart_data(labels, {"users": users_data}, {"RPS": rps_data}, "count")
    }


def create_benchmark_dataset(args):
    build_ids = args['id[]']
    req = args.get('request')
    calculation = args.get('calculation')
    aggregator = args.get('aggregator')
    status = args.get("status", 'all')
    if not aggregator or aggregator == 'auto':
        aggregator = '1s'
    tests_meta = APIReport.query.filter(APIReport.id.in_(build_ids)).order_by(APIReport.vusers.asc()).all()
    labels = set()
    data = {}
    y_axis = ''
    for _ in tests_meta:
        try:
            labels.add(_.vusers)
            if _.environment not in data:
                data[_.environment] = {}
            if calculation == 'throughput':
                y_axis = 'Requests per second'
                data[_.environment][str(_.vusers)] = get_throughput_per_test(
                    _.build_id, _.name, _.lg_type, "", req, aggregator, status)
            elif calculation != ['throughput']:
                y_axis = 'Response time, ms'
                if calculation == 'errors':
                    y_axis = 'Errors'
                data[_.environment][str(_.vusers)] = get_response_time_per_test(
                    _.build_id, _.name, _.lg_type, "", req, calculation, status)
            else:
                data[_.environment][str(_.vusers)] = None
        except IndexError:
            pass

    labels = [""] + sorted(list(labels)) + [""]
    return {"data": chart_data(labels, [], data, "data"), "label": y_axis}
