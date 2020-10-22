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

from influxdb import InfluxDBClient
from datetime import datetime, timezone
from galloper.constants import str_to_timestamp
from galloper.dal.vault import get_project_hidden_secrets, get_project_secrets
from galloper.database.models.api_reports import APIReport


def get_client(project_id, db_name=None):
    secrets = get_project_secrets(project_id)
    hidden_secrets = get_project_hidden_secrets(project_id)
    influx_user = secrets.get("influx_user") if "influx_user" in secrets else hidden_secrets.get("influx_user", "")
    influx_password = secrets.get("influx_password") if "influx_password" in secrets else \
        hidden_secrets.get("influx_password", "")

    return InfluxDBClient("carrier-influx", 8086, influx_user, influx_password, db_name)


def get_test_details(project_id, build_id, test_name, lg_type):
    test = {
        "start_time": 0,
        "name": test_name,
        "environment": "",
        "type": "",
        "end_time": 0,
        "failures": 0,
        "total": 0,
        "thresholds_missed": 0,
        "throughput": 0,
        "vusers": 0,
        "pct95": 0,
        "duration": 0,
        "1xx": 0,
        "2xx": 0,
        "3xx": 0,
        "4xx": 0,
        "5xx": 0,
        "build_id": build_id,
        "lg_type": lg_type,
        "requests": []
    }
    q_start_time = f"select time, active from {lg_type}..\"users\" " \
                   f"where build_id='{build_id}' order by time asc limit 1"
    q_end_time = f"select time, active from {lg_type}..\"users\" " \
                 f"where build_id='{build_id}' order by time desc limit 1"
    q_response_codes = f"select sum(\"1xx\") as \"1xx\", sum(\"2xx\") as \"2xx\", sum(\"3xx\") as \"3xx\", " \
                       f"sum(\"4xx\") as \"4xx\", sum(\"5xx\") as \"5xx\", sum(\"ko\") as KO, " \
                       f"sum(\"total\") as Total, sum(throughput) as \"throughput\" " \
                       f"from comparison..api_comparison where build_id='{build_id}'"
    q_total_users = f"show tag values on comparison with key=\"users\" where build_id='{build_id}'"
    q_env = f"show tag values on comparison with key=\"env\" where build_id='{build_id}'"
    q_type = f"show tag values on comparison with key=\"test_type\" where build_id='{build_id}'"
    q_pct95 = f"select percentile(response_time, 95) from {lg_type}..{test_name} " \
              f"where build_id='{build_id}' and status='OK'"
    q_requests_name = f"show tag values on comparison with key=\"request_name\" " \
                      f"where build_id='{build_id}'"
    client = get_client(project_id)
    test["start_time"] = list(client.query(q_start_time)["users"])[0]["time"]
    test["end_time"] = list(client.query(q_end_time)["users"])[0]["time"]
    test["duration"] = round(str_to_timestamp(test["end_time"]) - str_to_timestamp(test["start_time"]), 1)
    test["vusers"] = list(client.query(q_total_users)["api_comparison"])[0]["value"]
    test["environment"] = list(client.query(q_env)["api_comparison"])[0]["value"]
    test["type"] = list(client.query(q_type)["api_comparison"])[0]["value"]
    pct95 = list(client.query(q_pct95)[test_name])
    test["pct95"] = pct95[0]["percentile"] if pct95 else 0
    test["requests"] = [name["value"] for name in client.query(q_requests_name)["api_comparison"]]
    response_data = list(client.query(q_response_codes)['api_comparison'])[0]
    test['total'] = response_data['Total']
    test['failures'] = response_data['KO']
    test['throughput'] = round(response_data['throughput'], 1)
    test['1xx'] = response_data['1xx']
    test['2xx'] = response_data['2xx']
    test['3xx'] = response_data['3xx']
    test['4xx'] = response_data['4xx']
    test['5xx'] = response_data['5xx']
    return test


def get_sampler_types(project_id, build_id, test_name, lg_type):
    q_samplers = f"show tag values on {lg_type} with key=sampler_type where build_id='{build_id}'"
    client = get_client(project_id)
    return [each["value"] for each in list(client.query(q_samplers)[test_name])]


def get_backend_users(project_id, build_id, lg_type, start_time, end_time, aggregation):
    query = f"select sum(\"max\") from (select max(\"active\") from {lg_type}..\"users\" " \
            f"where build_id='{build_id}' group by lg_id) " \
            f"WHERE time>='{start_time}' and time<='{end_time}' GROUP BY time(1s)"
    client = get_client(project_id)
    res = client.query(query)['users']
    timestamps = []
    results = {"users": {}}
    # aggregation of users
    _tmp = []
    if 'm' in aggregation:
        aggregation = f"{str(int(aggregation.replace('m', ''))*60)}s"
    for _ in res:
        _tmp.append(_['sum'] if _['sum'] else 0)
        results["users"][_['time']] = None
        if _['time'] not in timestamps:
            timestamps.append(_['time'])
        if (len(_tmp) % int(aggregation.replace('s', ''))) == 0:
            results["users"][_['time']] = max(_tmp)
            _tmp = []
    return timestamps, results


def get_backend_requests(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                         timestamps=None, users=None, scope=None, aggr='pct95', status='all'):
    """
    :param build_id: - could be obtained from control_tower during tests execution
    :param test_name: - name of the test used as measurement in database
    :param lg_type: - either jmeter or gatling as a DB name
    :param start_time
    :param end_time
    :return:

    """
    scope_addon = ""
    status_addon = ""
    group_by = ""
    project_id = get_project_id(build_id)
    if aggr in ["Min", "Max"]:
        aggr_func = f"{aggr.lower()}(response_time)"
    elif 'pct' in aggr:
        aggr = aggr.replace('pct', '')
        aggr_func = f"percentile(response_time, {aggr})"
    else:
        aggr_func = f"percentile(response_time, 50)"

    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    elif scope != 'All':
        group_by = "request_name, "

    if status != 'all':
        status_addon = f" and status='{status.upper()}'"

    if not (timestamps and users):
        timestamps, users = get_backend_users(project_id, build_id, lg_type, start_time, end_time, aggregation)
    query = f"select time, {group_by}{aggr_func} as rt from {lg_type}..{test_name} " \
            f"where time>='{start_time}' and time<='{end_time}' {status_addon} and sampler_type='{sampler}' and " \
            f"build_id='{build_id}' {scope_addon} group by {group_by}time({aggregation})"
    res = get_client(project_id).query(query)[test_name]
    results = {}
    if group_by:
        for _ in res:
            if not _.get('request_name'):
                continue
            if _['request_name'] not in results:
                results[_['request_name']] = {}
                for ts in timestamps:
                    results[_['request_name']][ts] = None
            results[_['request_name']][_['time']] = _['rt']
    else:
        results['response'] = {}
        for ts in timestamps:
            results['response'][ts] = None
        for _ in res:
            results['response'][_['time']] = _['rt']
    return timestamps, results, users


def get_response_time_per_test(build_id, test_name, lg_type, sampler, scope, aggr, status='all'):
    scope_addon = ""
    group_by = ""
    sampler_piece = ""
    status_addon = ""
    project_id = get_project_id(build_id)
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    elif scope != 'All':
        group_by += "group by request_name"
    if aggr in ["min", "max", "mean"]:
        aggr_func = f"{aggr.lower()}(response_time)"
    elif 'pct' in aggr:
        aggr = aggr.replace('pct', '')
        aggr_func = f"percentile(response_time, {aggr})"
    elif 'errors' in aggr:
        aggr_func = 'sum(errorCount)'
    elif 'total' in aggr:
        aggr_func = 'count(response_time)'
    else:
        aggr_func = f"percentile(response_time, 50)"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    if sampler:
        sampler_piece = f"sampler_type='{sampler}' and "
    query = f"select {aggr_func} as rt from {lg_type}..{test_name} where {sampler_piece}" \
            f"build_id='{build_id}'{status_addon} {scope_addon} {group_by}"
    return round(list(get_client(project_id).query(query)[test_name])[0]["rt"], 2)


def get_throughput_per_test(build_id, test_name, lg_type, sampler, scope, aggregator, status='all'):
    scope_addon = ""
    group_by_addon = ""
    sampler_piece = ""
    status_addon = ""
    project_id = get_project_id(build_id)
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    elif scope != 'All':
        group_by_addon = "request_name"
    if sampler:
        sampler_piece = f"sampler_type='{sampler}' and"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    group_by = f"group by {group_by_addon} time({aggregator})"
    query = f"select mean(rt) as throughput from (" \
            f"select count(response_time) as rt from {lg_type}..{test_name} " \
            f"where {sampler_piece} build_id='{build_id}'{status_addon} {scope_addon} {group_by} " \
            f")"
    return round(list(get_client(project_id).query(query)[test_name])[0]["throughput"], 2)


def get_tps(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
            timestamps=None, users=None, scope=None, status='all'):
    project_id = get_project_id(build_id)
    if not (timestamps and users):
        timestamps, users = get_backend_users(project_id, build_id, lg_type, start_time, end_time, aggregation)
    scope_addon = ""
    status_addon = ""
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    responses_query = f"select time, count(response_time) from {lg_type}..{test_name} where time>='{start_time}' " \
                      f"and time<='{end_time}' and sampler_type='{sampler}' {status_addon} and build_id='{build_id}' " \
                      f"{scope_addon} group by time({aggregation}) fill(0)"
    res = get_client(project_id).query(responses_query)[test_name]
    results = {"responses": {}}
    for _ in timestamps:
        results['responses'][_] = None
    for _ in res:
        results['responses'][_['time']] = _['count']
    return timestamps, results, users


def get_response_codes(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                       timestamps=None, users=None, scope=None, aggr="2xx", status='all'):
    project_id = get_project_id(build_id)
    if not (timestamps and users):
        timestamps, users = get_backend_users(project_id, build_id, lg_type, start_time, end_time, aggregation)
    scope_addon = f"and status_code=~/^{aggr[0]}/ "
    status_addon = ""
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    rcode_query = f"select time, count(status_code) from {lg_type}..{test_name} where build_id='{build_id}' " \
                  f"and sampler_type='{sampler}' and time>='{start_time}' and time<='{end_time}'{status_addon} " \
                  f"{scope_addon} group by time({aggregation})"
    res = get_client(project_id).query(rcode_query)[test_name]
    results = {"rcodes": {}}
    for _ in timestamps:
        results['rcodes'][_] = None
    for _ in res:
        results['rcodes'][_['time']] = _["count"]
    return timestamps, results, users


def get_errors(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
               timestamps=None, users=None, scope=None):
    project_id = get_project_id(build_id)
    if not (timestamps and users):
        timestamps, users = get_backend_users(project_id, build_id, lg_type, start_time, end_time, aggregation)
    scope_addon = ""
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    error_query = f"select time, count(status) from {lg_type}..{test_name} " \
                  f"where time>='{start_time}' and time<='{end_time}' and sampler_type='{sampler}' and" \
                  f" build_id='{build_id}' and status='KO' {scope_addon} group by time(1s)"
    results = {"errors": {}}
    for _ in timestamps:
        results['errors'][_] = None
    res = get_client(project_id).query(error_query)[test_name]
    _tmp = []
    if 'm' in aggregation:
        aggregation = f"{str(int(aggregation.replace('m', ''))*60)}s"
    for _ in res:
        _tmp.append(_['count'])
        if (len(_tmp) % int(aggregation.replace('s', ''))) == 0:
            results['errors'][_['time']] = sum(_tmp)
            _tmp = []
    return timestamps, results, users


def get_hits(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
             timestamps=None, users=None, scope=None, status='all'):
    project_id = get_project_id(build_id)
    if not (timestamps and users):
        timestamps, users = get_backend_users(project_id, build_id, lg_type, start_time, end_time, aggregation)
    scope_addon = ""
    status_addon = ""
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    hits_query = f"select hit from {lg_type}..{test_name} where " \
                 f"time>='{start_time}' and time<='{end_time}'{status_addon} and sampler_type='{sampler}' and" \
                 f" build_id='{build_id}' {scope_addon}"
    results = {"hits": {}}
    res = get_client(project_id).query(hits_query)[test_name]
    for _ in res:
        hit_time = datetime.fromtimestamp(float(_["hit"]), tz=timezone.utc)
        if hit_time.strftime("%Y-%m-%dT%H:%M:%SZ") in results['hits']:
            results['hits'][hit_time.strftime("%Y-%m-%dT%H:%M:%SZ")] += 1
        else:
            results['hits'][hit_time.strftime("%Y-%m-%dT%H:%M:%SZ")] = 1
    # aggregation of hits
    _tmp = []
    if 'm' in aggregation:
        aggregation = f"{str(int(aggregation.replace('m', ''))*60)}s"
    _ts = None
    for _ in results['hits']:
        if len(_tmp) == 0:
            _ts = _
        _tmp.append(results['hits'][_])
        results['hits'][_] = None
        if (len(_tmp) % int(aggregation.replace('s', ''))) == 0:
            results['hits'][_ts] = float(sum(_tmp))
            _tmp = []
            _ts = None
    return timestamps, results, users


def get_hits_tps(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler, status='all'):
    project_id = get_project_id(build_id)
    timestamps, users = get_backend_users(project_id, build_id, lg_type, start_time, end_time, aggregation)
    results = {"responses": {}, "hits": {}}
    _, responses, _ = get_tps(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                              timestamps, users, status=status)
    results['responses'] = responses['responses']
    _, hits, _ = get_hits(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                          timestamps, users, status=status)
    results['hits'] = hits['hits']
    return timestamps, results, users


def average_responses(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler, status='all'):
    project_id = get_project_id(build_id)
    timestamps, users = get_backend_users(project_id, build_id, lg_type, start_time, end_time, aggregation)
    status_addon = ""
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    responses_query = f"select time, percentile(response_time, 95) from {lg_type}..{test_name} " \
                      f"where time>='{start_time}' " \
                      f"and time<='{end_time}' and sampler_type='{sampler}'{status_addon} and " \
                      f"build_id='{build_id}' group by time({aggregation})"
    res = get_client(project_id).query(responses_query)[test_name]
    results = {"responses": {}}
    for _ in timestamps:
        results['responses'][_] = None
    for _ in res:
        results["responses"][_['time']] = _['percentile']
    return timestamps, results, users


def get_build_data(build_id, test_name, lg_type, start_time, end_time, sampler, status='all'):
    status_addon = ""
    project_id = get_project_id(build_id)
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    requests_in_range = f"select time, request_name, max(response_time) from {lg_type}..{test_name} " \
                        f"where time>='{start_time}' " \
                        f"and time<='{end_time}' and sampler_type='{sampler}'{status_addon} and " \
                        f"build_id='{build_id}' group by request_name"
    res = get_client(project_id).query(requests_in_range)[test_name]
    requests_names = [f"'{each['request_name']}'" for each in res]
    if len(requests_names) > 1:
        requests = f'[{"|".join(requests_names)}]'
    elif requests_names:
        requests = requests_names[0].replace("'", "")
    else:
        return []
    query = f"select * from comparison..api_comparison where build_id='{build_id}' and request_name=~/^{requests}/"
    return list(get_client(project_id).query(query)['api_comparison'])


def delete_test_data(build_id, test_name, lg_type):
    project_id = get_project_id(build_id)
    query_one = f"DELETE from {test_name} where build_id='{build_id}'"
    query_two = f"DELETE from api_comparison where build_id='{build_id}'"
    query_three = f"DELETE from api_comparison where build_id='audit_{test_name}_{build_id}'"
    client = get_client(project_id, lg_type)
    client.query(query_one)
    client.close()
    client = get_client(project_id, 'comparison')
    client.query(query_two)
    client.query(query_three)
    client.close()
    return True


def get_threholds(test_name, environment):
    query = f'select time, scope, target, aggregation, comparison, yellow, red from thresholds..thresholds ' \
            f'where "simulation"=\'{test_name}\' and "environment"=\'{environment}\' order by time'
    return list(get_client().query(query)['thresholds'])


def _create_threshold(test, environment, scope, target, aggregation, comparison, yellow, red, client):
    json_body = [{
        "measurement": "thresholds",
        "tags": {
            "simulation": test,
            "environment": environment,
            "scope": scope,
            "target": target,
            "aggregation": aggregation,
            "comparison": comparison
        },
        "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": {
            "yellow": yellow,
            "red": red
        }
    }]
    return client.write_points(json_body)


def _delete_threshold(test, environment, target, scope, aggregation, comparison, client):
    query = f"DELETE from thresholds where simulation='{test}' and environment='{environment}' " \
            f"and target='{target}' and scope='{scope}' " \
            f"and aggregation='{aggregation}' and comparison='{comparison}'"
    return client.query(query)


def create_thresholds(test, environment, scope, target, aggregation, comparison, yellow, red):
    client = get_client('thresholds')
    res = _create_threshold(test, environment, scope, target, aggregation, comparison, yellow, red, client)
    client.close()
    return res


def delete_threshold(test, environment, target, scope, aggregation, comparison):
    client = get_client('thresholds')
    _delete_threshold(test, environment, target, scope, aggregation, comparison, client)
    client.close()
    return True


def get_aggregated_test_results(test, build_id):
    project_id = get_project_id(build_id)
    query = f"SELECT * from api_comparison where simulation='{test}' and build_id='{build_id}'"
    return list(get_client(project_id, 'comparison').query(query))


def get_baseline(test):
    query = f"SELECT * from api_comparison where build_id=~/audit_{test}_/"
    return list(get_client('comparison').query(query))


def delete_baseline(build_id):
    query = f"DELETE from api_comparison where build_id='{build_id}'"
    return get_client('comparison').query(query)


def set_baseline(request):
    json_body = [{
        "measurement": "api_comparison",
        "tags": {
            "build_id": f"audit_{request['simulation']}_{request['build_id']}",
            "duration": request['duration'],
            "env": request['env'],
            "method": request['method'],
            "request_name": request['request_name'],
            "simulation": request['simulation'],
            "test_type": request['test_type'],
            "users": request['users']
        },
        "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": {
            "1xx": int(request['1xx']),
            "2xx": int(request['2xx']),
            "3xx": int(request['3xx']),
            "4xx": int(request['4xx']),
            "5xx": int(request['5xx']),
            "NaN": int(request['NaN']),
            "ko": int(request['ko']),
            "ok": int(request['ok']),
            "pct50": int(request['pct50']),
            "pct75": int(request['pct75']),
            "pct90": int(request['pct90']),
            "pct95": int(request['pct95']),
            "pct99": int(request['pct99']),
            "total": int(request['total']),
            "max": float(request['max']),
            "mean": float(request['mean']),
            "min": float(request['min']),
            "throughput": float(request['throughput']),
            "report_id": int(request['report_id'])
        }
    }]
    project_id = get_project_id(request['build_id'])
    return get_client(project_id, 'comparison').write_points(json_body)


def get_project_id(build_id):
    return APIReport.query.filter_by(build_id=build_id).first().to_json()["project_id"]
