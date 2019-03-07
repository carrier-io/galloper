import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from influxdb import InfluxDBClient
from jinja2 import Environment, FileSystemLoader


def get_last_builds(args):
    client = InfluxDBClient(args['influx_host'], args['influx_port'], username=args['influx_user'],
                            password=args['influx_password'], database=args['influx_comparison_database'])
    tests_data = []
    build_ids = []
    last_builds = client.query("select distinct(id) from (select build_id as id, pct95 from api_comparison "
                               "where simulation=\'" + args['simulation'] + "\' and test_type=\'" + args['test_type'] +
                               "\' and \"users\"=\'" + str(args['users']) + "\' and build_id!~/audit_"
                               + args['simulation'] + "_/ order by time DESC) GROUP BY time(1s) order by DESC limit "
                               + str(args['test_limit']))
    for test in list(last_builds.get_points()):
        build_ids.append(test['distinct'])

    for id in build_ids:
        test_data = client.query("select * from api_comparison where build_id=\'" + id + "\'")
        tests_data.append(test_data)
    client.close()
    return tests_data


def get_baseline(args):
    client = InfluxDBClient(args['influx_host'], args['influx_port'], username=args['influx_user'],
                            password=args['influx_password'], database=args['influx_comparison_database'])
    baseline_build_id = client.query("select last(pct95), build_id from api_comparison where simulation=\'"
                                     + args['simulation'] + "\' and test_type=\'" + args['test_type'] +
                                     "\' and \"users\"=\'" + str(args['users']) + "\' and build_id=~/audit_"
                                     + args['simulation'] + "_/")
    result = list(baseline_build_id.get_points())
    if result.__len__() == 0:
        print("Baseline not found")
        return None
    id = result[0]['build_id']
    baseline_data = client.query("select * from api_comparison where build_id=\'" + id + "\'")
    client.close()
    return list(baseline_data.get_points())


def append_thresholds_to_test_data(test, args):
    client = InfluxDBClient(args['influx_host'], args['influx_port'], username=args['influx_user'],
                            password=args['influx_password'], database=args['influx_thresholds_database'])
    params = ['request_name', 'total', 'throughput', 'ko', 'min', 'max', 'pct50', 'pct75', 'pct95', 'time',
              'simulation', 'users', 'duration']
    test_summary = []
    for request in test:
        request_data = {}
        threshold = client.query("select last(red) as red, last(yellow) as yellow from threshold where request_name=\'"
                                 + str(request['request_name']) + "\'")
        if list(threshold.get_points()).__len__() == 0:
            red_treshold = 1000
            yellow_treshold = 450
        else:
            red_treshold = int(list(threshold.get_points())[0]['red'])
            yellow_treshold = int(list(threshold.get_points())[0]['yellow'])

        if int(request['pct50']) < yellow_treshold:
            request_data['pct50_threshold'] = 'green'
        else:
            request_data['pct50_threshold'] = 'orange'
        if int(request['pct50']) >= red_treshold:
            request_data['pct50_threshold'] = 'red'

        if int(request['pct75']) < yellow_treshold:
            request_data['pct75_threshold'] = 'green'
        else:
            request_data['pct75_threshold'] = 'orange'
        if int(request['pct75']) >= red_treshold:
            request_data['pct75_threshold'] = 'red'

        if int(request['pct95']) < yellow_treshold:
            request_data['pct95_threshold'] = 'green'
        else:
            request_data['pct95_threshold'] = 'orange'
        if int(request['pct95']) >= red_treshold:
            request_data['pct95_threshold'] = 'red'

        if int(request['min']) < yellow_treshold:
            request_data['min_threshold'] = 'green'
        else:
            request_data['min_threshold'] = 'orange'
        if int(request['min']) >= red_treshold:
            request_data['min_threshold'] = 'red'

        if int(request['max']) < yellow_treshold:
            request_data['max_threshold'] = 'green'
        else:
            request_data['max_threshold'] = 'orange'
        if int(request['max']) >= red_treshold:
            request_data['max_threshold'] = 'red'

        request_data['yellow_threshold_value'] = yellow_treshold
        request_data['red_threshold_value'] = red_treshold
        for param in params:
            request_data[param] = request[param]
        test_summary.append(request_data)
    client.close()
    return test_summary
