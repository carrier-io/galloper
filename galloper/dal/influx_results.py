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
from galloper.constants import str_to_timestamp, MAX_DOTS_ON_CHART
from galloper.dal.vault import get_project_hidden_secrets, get_project_secrets
from galloper.database.models.api_reports import APIReport
from flask import current_app


def get_client(project_id, db_name=None):
    secrets = get_project_secrets(project_id)
    hidden_secrets = get_project_hidden_secrets(project_id)
    influx_host = secrets.get("influx_ip") if "influx_ip" in secrets else hidden_secrets.get("influx_ip", "")
    influx_user = secrets.get("influx_user") if "influx_user" in secrets else hidden_secrets.get("influx_user", "")
    influx_password = secrets.get("influx_password") if "influx_password" in secrets else \
        hidden_secrets.get("influx_password", "")

    return InfluxDBClient(influx_host, 8086, influx_user, influx_password, db_name)


def create_project_databases(project_id):
    hidden_secrets = get_project_hidden_secrets(project_id)
    db_list = [hidden_secrets.get("jmeter_db"), hidden_secrets.get("gatling_db"), hidden_secrets.get("comparison_db"),
               hidden_secrets.get("telegraf_db")]
    client = get_client(project_id)
    for each in db_list:
        client.query(f"create database {each} with duration 180d replication 1 shard duration 7d name autogen")


def drop_project_databases(project_id):
    hidden_secrets = get_project_hidden_secrets(project_id)
    db_list = [hidden_secrets.get("jmeter_db"), hidden_secrets.get("gatling_db"), hidden_secrets.get("comparison_db"),
               hidden_secrets.get("telegraf_db")]
    client = get_client(project_id)
    for each in db_list:
        client.query(f"drop database {each}")


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
    q_start_time = f"select time, active from {lg_type}_{project_id}..\"users\" " \
                   f"where build_id='{build_id}' order by time asc limit 1"
    q_end_time = f"select time, active from {lg_type}_{project_id}..\"users\" " \
                 f"where build_id='{build_id}' order by time desc limit 1"
    q_response_codes = f"select \"1xx\", \"2xx\", \"3xx\", \"4xx\", \"5xx\", \"ko\" as KO, " \
                       f"\"total\" as Total, \"throughput\" from comparison_{project_id}..api_comparison " \
                       f"where build_id='{build_id}' and request_name='All'"
    q_total_users = f"show tag values on comparison_{project_id} with key=\"users\" where build_id='{build_id}'"
    q_env = f"show tag values on comparison_{project_id} with key=\"env\" where build_id='{build_id}'"
    q_type = f"show tag values on comparison_{project_id} with key=\"test_type\" where build_id='{build_id}'"
    q_requests_name = f"show tag values on comparison_{project_id} with key=\"request_name\" " \
                      f"where build_id='{build_id}'"
    client = get_client(project_id)
    test["start_time"] = list(client.query(q_start_time)["users"])[0]["time"]
    test["end_time"] = list(client.query(q_end_time)["users"])[0]["time"]
    test["duration"] = round(str_to_timestamp(test["end_time"]) - str_to_timestamp(test["start_time"]), 1)
    test["vusers"] = list(client.query(q_total_users)["api_comparison"])[0]["value"]
    test["environment"] = list(client.query(q_env)["api_comparison"])[0]["value"]
    test["type"] = list(client.query(q_type)["api_comparison"])[0]["value"]
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


def calculate_auto_aggregation(build_id, test_name, lg_type, start_time, end_time):
    project_id = get_project_id(build_id)
    client = get_client(project_id)
    aggregation = "1s"
    aggr_list = ["1s", "5s", "30s", "1m", "5m", "10m"]
    for i in range(len(aggr_list)):
        aggr = aggr_list[i]
        query = f"select sum(\"count\") from (select count(pct95) from {lg_type}_{project_id}..{test_name}_{aggr} " \
                f"where time>='{start_time}' and time<='{end_time}' and build_id='{build_id}' group by time({aggr}))"
        result = list(client.query(query)[f"{test_name}_{aggr}"])
        if result:
            if int(result[0]["sum"]) > MAX_DOTS_ON_CHART and aggregation != "10m":
                aggregation = aggr_list[i + 1]
            if int(result[0]["sum"]) == 0 and aggregation != "1s":
                aggregation = "30s"
                break
    return aggregation


def get_sampler_types(project_id, build_id, test_name, lg_type):
    q_samplers = f"show tag values on {lg_type}_{project_id} with key=sampler_type where build_id='{build_id}'"
    client = get_client(project_id)
    return [each["value"] for each in list(client.query(q_samplers)[f"{test_name}_1s"])]


def get_backend_users(build_id, lg_type, start_time, end_time, aggregation):
    project_id = get_project_id(build_id)
    query = f"select sum(\"max\") from (select max(\"active\") from {lg_type}_{project_id}..\"users_{aggregation}\" " \
            f"where build_id='{build_id}' group by lg_id) " \
            f"WHERE time>='{start_time}' and time<='{end_time}' GROUP BY time(1s)"
    client = get_client(project_id)
    res = client.query(query)[f'users_{aggregation}']
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
    aggr = aggr.lower()

    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    elif scope != 'All':
        group_by = "request_name, "

    if status != 'all':
        status_addon = f" and status='{status.upper()}'"

    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, lg_type, start_time, end_time, aggregation)
    query = f"select time, {group_by}percentile(\"{aggr}\", 95) as rt from {lg_type}_{project_id}..{test_name}_{aggregation} " \
            f"where time>='{start_time}' and time<='{end_time}' {status_addon} and sampler_type='{sampler}' and " \
            f"build_id='{build_id}' {scope_addon} group by {group_by}time({aggregation})"
    res = get_client(project_id).query(query)[f"{test_name}_{aggregation}"]
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


def get_response_time_per_test(build_id, test_name, lg_type, sampler, scope, aggr, status='all', aggregator="30s"):
    scope_addon = ""
    group_by = ""
    sampler_piece = ""
    status_addon = ""
    project_id = get_project_id(build_id)
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    elif scope != 'All':
        group_by += "group by request_name"
    if aggr in ["min", "max", "median", "pct95", "pct99"]:
        aggr_func = f"percentile(\"{aggr}\", 95)"
    else:
        aggr_func = 'sum(total)'

    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    if 'errors' in aggr:
        status_addon = " and status='KO'"
    if sampler:
        sampler_piece = f"sampler_type='{sampler}' and "
    query = f"select {aggr_func} as rt from {lg_type}_{project_id}..{test_name}_{aggregator} where {sampler_piece}" \
            f"build_id='{build_id}'{status_addon} {scope_addon} {group_by}"
    return round(list(get_client(project_id).query(query)[f"{test_name}_{aggregator}"])[0]["rt"], 2)


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
            f"select sum(total) as rt from {lg_type}_{project_id}..{test_name}_{aggregator} " \
            f"where {sampler_piece} build_id='{build_id}'{status_addon} {scope_addon} {group_by} " \
            f")"
    return round(list(get_client(project_id).query(query)[f"{test_name}_{aggregator}"])[0]["throughput"], 2)


def get_tps(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
            timestamps=None, users=None, scope=None, status='all'):
    project_id = get_project_id(build_id)
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, lg_type, start_time, end_time, aggregation)
    scope_addon = ""
    status_addon = ""
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    responses_query = f"select time, sum(total) from {lg_type}_{project_id}..{test_name}_{aggregation}" \
                      f" where time>='{start_time}' " \
                      f"and time<='{end_time}' and sampler_type='{sampler}' {status_addon} and build_id='{build_id}' " \
                      f"{scope_addon} group by time({aggregation})"
    res = get_client(project_id).query(responses_query)[f"{test_name}_{aggregation}"]
    results = {"responses": {}}
    for _ in timestamps:
        results['responses'][_] = None
    for _ in res:
        results['responses'][_['time']] = _['sum']
    return timestamps, results, users


def get_response_codes(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                       timestamps=None, users=None, scope=None, aggr="2xx", status='all'):
    project_id = get_project_id(build_id)
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, lg_type, start_time, end_time, aggregation)
    scope_addon = ""
    status_addon = " "
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}' "
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    rcode_query = f"select time, sum(\"{aggr}\") from {lg_type}_{project_id}..{test_name}_{aggregation}" \
                  f" where build_id='{build_id}' " \
                  f"and sampler_type='{sampler}' and time>='{start_time}' and time<='{end_time}'{status_addon} " \
                  f"{scope_addon}group by time({aggregation})"
    res = get_client(project_id).query(rcode_query)[f"{test_name}_{aggregation}"]
    results = {"rcodes": {}}
    for _ in timestamps:
        results['rcodes'][_] = None
    for _ in res:
        results['rcodes'][_['time']] = _["sum"]
    return timestamps, results, users


def get_errors(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
               timestamps=None, users=None, scope=None):
    project_id = get_project_id(build_id)
    if not (timestamps and users):
        timestamps, users = get_backend_users(build_id, lg_type, start_time, end_time, aggregation)
    scope_addon = ""
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    error_query = f"select time, count(status) from {lg_type}_{project_id}..{test_name}_{aggregation} " \
                  f"where time>='{start_time}' and time<='{end_time}' and sampler_type='{sampler}' and" \
                  f" build_id='{build_id}' and status='KO' {scope_addon} group by time(1s)"
    results = {"errors": {}}
    for _ in timestamps:
        results['errors'][_] = None
    res = get_client(project_id).query(error_query)[f"{test_name}_{aggregation}"]
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
        timestamps, users = get_backend_users(build_id, lg_type, start_time, end_time, aggregation)
    scope_addon = ""
    status_addon = ""
    if scope and scope != 'All':
        scope_addon = f"and request_name='{scope}'"
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    hits_query = f"select hit from {lg_type}_{project_id}..{test_name} where " \
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
    timestamps, users = get_backend_users(build_id, lg_type, start_time, end_time, aggregation)
    results = {"throughput": {}}
    _, responses, _ = get_tps(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
                              timestamps, users, status=status)
    results['throughput'] = responses['responses']
    # _, hits, _ = get_hits(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler,
    #                       timestamps, users, status=status)
    # results['hits'] = hits['hits']
    return timestamps, results, users


def average_responses(build_id, test_name, lg_type, start_time, end_time, aggregation, sampler, status='all'):
    project_id = get_project_id(build_id)
    timestamps, users = get_backend_users(build_id, lg_type, start_time, end_time, aggregation)
    status_addon = ""
    if status != 'all':
        status_addon = f" and status='{status.upper()}'"
    responses_query = f"select time, percentile(\"pct95\", 95) from {lg_type}_{project_id}..{test_name}_{aggregation} " \
                      f"where time>='{start_time}' " \
                      f"and time<='{end_time}' and sampler_type='{sampler}'{status_addon} and " \
                      f"build_id='{build_id}' group by time({aggregation})"
    res = get_client(project_id).query(responses_query)[f"{test_name}_{aggregation}"]
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
    requests_in_range = f"select time, request_name, max(pct95) from {lg_type}_{project_id}..{test_name}_5s " \
                        f"where time>='{start_time}' " \
                        f"and time<='{end_time}' and sampler_type='{sampler}'{status_addon} and " \
                        f"build_id='{build_id}' group by request_name"
    res = get_client(project_id).query(requests_in_range)[f"{test_name}_5s"]
    requests_names = [f"'{each['request_name']}'" for each in res]
    escaped_requests_names = []
    for each in requests_names:
        for _ in ["[", "]", "-", "/"]:
            each = each.replace(_, f"\\{_}")
        escaped_requests_names.append(each)
    if len(escaped_requests_names) > 1:
        requests = f'[{"|".join(escaped_requests_names)}]'
    elif escaped_requests_names:
        requests = escaped_requests_names[0].replace("'", "")
    else:
        return []
    query = f"select * from comparison_{project_id}..api_comparison where build_id='{build_id}' and request_name=~/^{requests}/"
    return list(get_client(project_id).query(query)['api_comparison'])


def delete_test_data(build_id, test_name, lg_type):
    project_id = get_project_id(build_id)
    query_one = f"DELETE from {test_name} where build_id='{build_id}'"
    query_two = f"DELETE from api_comparison where build_id='{build_id}'"
    client = get_client(project_id, f"{lg_type}_{project_id}")
    client.query(query_one)
    client.close()
    client = get_client(project_id, f'comparison_{project_id}')
    client.query(query_two)
    client.close()
    return True


def get_aggregated_test_results(test, build_id):
    project_id = get_project_id(build_id)
    query = f"SELECT * from api_comparison where simulation='{test}' and build_id='{build_id}'"
    return list(get_client(project_id, f'comparison_{project_id}').query(query))


def get_project_id(build_id):
    return APIReport.query.filter_by(build_id=build_id).first().to_json()["project_id"]
