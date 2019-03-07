import time
import calendar
import datetime
from chart_generator import alerts_linechart, barchart
from email.MIMEImage import MIMEImage
from os import path, getcwd, makedirs
from shutil import rmtree


def create_test_description(test, baseline, comparison_metric):
    params = ['simulation', 'users', 'duration']
    test_params = {}
    for param in params:
        test_params[param] = test[0][param]
    test_params['end'] = str(test[0]['time']).replace("T", " ").replace("Z", "")
    timestamp = calendar.timegm(time.strptime(test_params['end'], '%Y-%m-%d %H:%M:%S'))
    test_params['start'] = datetime.datetime.utcfromtimestamp(int(timestamp) - int(test[0]['duration']))\
        .strftime('%Y-%m-%d %H:%M:%S')
    test_params['status'], test_params['color'], test_params['failed_reason'] = check_status(test, baseline,
                                                                                             comparison_metric)
    return test_params


def check_status(test, baseline, comparison_metric):
    status, color, failed_message = check_functional_issues(test)
    if status is 'SUCCESS':
        status, color, failed_message = check_performance_degradation(test, baseline, comparison_metric)
    if status is 'SUCCESS':
        status, color, failed_message = check_missed_thresholds(test, comparison_metric)
    return status, color, failed_message


def check_functional_issues(test):
    request_count = 0
    error_count = 0
    for request in test:
        request_count += int(request['total'])
        error_count += int(request['ko'])
    error_rate = error_count * 100 / request_count
    if error_rate > 10:
        return 'FAILED', 'red', 'Failed reason: error rate - ' + str(error_rate) + ' %'
    return 'SUCCESS', 'green', ''


def check_performance_degradation(test, baseline, comparison_metric):
    if baseline:
        request_count = 0
        performance_degradation = 0
        for request in test:
            request_count += 1
            for baseline_request in baseline:
                if request['request_name'] == baseline_request['request_name']:
                    if int(request[comparison_metric]) < int(baseline_request[comparison_metric]):
                        performance_degradation += 1
        performance_degradation_rate = performance_degradation * 100 / request_count
        if performance_degradation_rate > 20:
            return 'FAILED', 'red', 'Failed reason: performance degradation rate - '\
                   + str(performance_degradation_rate) + ' %'
        else:
            return 'SUCCESS', 'green', ''
    else:
        return 'SUCCESS', 'green', ''


def check_missed_thresholds(test, comparison_metric):
    request_count = 0
    missed_thresholds = 0
    for request in test:
        request_count += 1
        if request[comparison_metric + '_threshold'] is not 'green':
            missed_thresholds += 1
    missed_thresholds_rate = missed_thresholds * 100 / request_count
    if missed_thresholds_rate > 50:
        return 'FAILED', 'red', 'Failed reason: missed thresholds rate - ' + str(missed_thresholds_rate) + ' %'
    return 'SUCCESS', 'green', ''


def create_builds_comparison(tests):
    builds_comparison = []
    for test in tests:
        test_info = {}
        request_count = 0
        total_request_count = 0
        avg_throughput = 0
        error_count = 0
        pct95 = 0
        for request in list(test.get_points()):
            request_count += 1
            total_request_count += int(request['total'])
            avg_throughput += float(request['throughput'])
            error_count += float(request['ko'])
            pct95 += int(request['pct95'])
        date = str(list(test.get_points())[0]['time']).replace("T", " ").replace("Z", "")
        timestamp = calendar.timegm(time.strptime(date, '%Y-%m-%d %H:%M:%S'))
        test_info['date'] = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%d-%b %H:%M')
        test_info['total'] = total_request_count
        test_info['throughput'] = round(avg_throughput / request_count, 2)
        test_info['pct95'] = pct95 / request_count
        test_info['error_rate'] = round((error_count / total_request_count) * 100, 2)
        builds_comparison.append(test_info)
    builds_comparison = calculate_diffs(builds_comparison)

    return builds_comparison


def calculate_diffs(builds):
    builds_comparison = []
    last_build = builds[0]
    for build in builds:
        build_info_with_diffs = compare_builds(build, last_build)
        builds_comparison.append(build_info_with_diffs)
    return builds_comparison


def compare_builds(build, last_build):
    build_info = {}
    params = ['date', 'error_rate', 'pct95', 'total', 'throughput']
    build_info['error_rate_diff'] = float(build['error_rate']) - float(last_build['error_rate'])
    if build_info['error_rate_diff'] > 0.0:
        build_info['error_rate_diff'] = "&#9650;" + str(build_info['error_rate_diff'])
    else:
        build_info['error_rate_diff'] = str(build_info['error_rate_diff']).replace("-", "&#9660;")
    build_info['pct95_diff'] = round(float(build['pct95']) * 100 / float(last_build['pct95']) - 100, 1)
    if build_info['pct95_diff'] > 0.0:
        build_info['pct95_diff'] = "&#9650;" + str(build_info['pct95_diff'])
    else:
        build_info['pct95_diff'] = str(build_info['pct95_diff']).replace("-", "&#9660;")
    build_info['total_diff'] = round(float(build['total']) * 100 / float(last_build['total']) - 100, 1)
    if build_info['total_diff'] > 0.0:
        build_info['total_diff'] = "&#9650;" + str(build_info['total_diff'])
    else:
        build_info['total_diff'] = str(build_info['total_diff']).replace("-", "&#9660;")
    build_info['throughput_diff'] = round(float(build['throughput']) * 100 / float(last_build['throughput']) - 100, 1)
    if build_info['throughput_diff'] > 0.0:
        build_info['throughput_diff'] = "&#9650;" + str(build_info['throughput_diff'])
    else:
        build_info['throughput_diff'] = str(build_info['throughput_diff']).replace("-", "&#9660;")

    for param in params:
        build_info[param] = build[param]
    return build_info


def create_charts(builds, last_test_data, baseline, comparison_metric):
    charts = []
    create_tmp_folder()
    charts.append(create_success_rate_chart(builds))
    charts.append(create_throughput_chart(builds))
    charts.append(create_comparison_vs_baseline_barchart(last_test_data, baseline, comparison_metric))
    charts.append(create_thresholds_chart(last_test_data, comparison_metric))
    return charts


def create_success_rate_chart(builds):
    values = []
    keys = []
    for test in builds:
        values.append(test['date'])
        keys.append(100 - test['error_rate'])
    datapoints = {
        'title': 'Successful requests, %',
        'label': 'Successful requests, %',
        'x_axis': 'Test Runs',
        'y_axis': 'Successful requests, %',
        'width': 10,
        'height': 3,
        'path_to_save': 'tmp/success_rate.png',
        'keys': keys[::-1],
        'values': [1, 2, 3, 4, 5],
        'labels': values[::-1]
    }
    alerts_linechart(datapoints)
    fp = open('tmp/success_rate.png', 'rb')
    image = MIMEImage(fp.read())
    image.add_header('Content-ID', '<success_rate>')
    fp.close()
    return image


def create_throughput_chart(builds):
    values = []
    keys = []
    for test in builds:
        values.append(test['date'])
        keys.append(test['throughput'])
    datapoints = {
        'title': 'Throughput',
        'label': 'Throughput, req/s',
        'x_axis': 'Test Runs',
        'y_axis': 'Throughput, req/s',
        'width': 10,
        'height': 3,
        'path_to_save': 'tmp/throughput.png',
        'keys': keys[::-1],
        'values': [1, 2, 3, 4, 5],
        'labels': values[::-1]
    }
    alerts_linechart(datapoints)
    fp = open('tmp/throughput.png', 'rb')
    image = MIMEImage(fp.read())
    image.add_header('Content-ID', '<throughput>')
    fp.close()
    return image


def create_comparison_vs_baseline_barchart(last_test_data, baseline, comparison_metric):
    green_keys = []
    yellow_keys = []
    utility_key = []
    green_request_value = []
    yellow_request_value = []
    utility_request_value = []
    green_request_name = []
    yellow_request_name = []
    utility_request_name = []
    count = 1
    for request in last_test_data:
        for baseline_request in baseline:
            if request['request_name'] == baseline_request['request_name']:
                if int(request[comparison_metric]) > int(baseline_request[comparison_metric]):
                    yellow_keys.append(count)
                    count += 1
                    yellow_request_value.append(round(-float(request[comparison_metric])/1000, 2))
                    yellow_request_name.append(request['request_name'])
                else:
                    green_keys.append(count)
                    count += 1
                    green_request_value.append(round(float(request[comparison_metric])/1000, 2))
                    green_request_name.append(request['request_name'])

    if green_keys.__len__() == 0:
        utility_key.append(count)
        count += 1
        utility_request_name.append('utility')
        utility_request_value.append(-max(yellow_request_value)/2)
    if yellow_keys.__len__() == 0:
        utility_key.append(count)
        count += 1
        utility_request_name.append('utility')
        utility_request_value.append(-max(green_request_value)/2)
    datapoints = {"green_keys": green_keys,
                  "yellow_keys": yellow_keys,
                  "red_keys": [],
                  "utility_keys": utility_key,
                  "green_request": green_request_value,
                  "yellow_request": yellow_request_value,
                  "red_request": [],
                  "utility_request": utility_request_value,
                  "green_request_name": green_request_name,
                  "yellow_request_name": yellow_request_name,
                  "red_request_name": [],
                  "utility_request_name": utility_request_name,
                  'width': 8,
                  'height': 4.5,
                  "x_axis": "Requests", "y_axis": "Time, s", "title": "Comparison vs Baseline",
                  "path_to_save": "tmp/baseline.png"}
    barchart(datapoints)
    fp = open('tmp/baseline.png', 'rb')
    image = MIMEImage(fp.read())
    image.add_header('Content-ID', '<baseline>')
    fp.close()
    return image


def create_thresholds_chart(last_test_data, comparison_metric):
    green_keys = []
    yellow_keys = []
    red_keys = []
    utility_key = []
    green_request_value = []
    yellow_request_value = []
    red_request_value = []
    utility_request_value = []
    green_request_name = []
    yellow_request_name = []
    red_request_name = []
    utility_request_name = []
    count = 1
    for request in last_test_data:
        if request[comparison_metric + '_threshold'] == 'green':
            green_keys.append(count)
            count += 1
            green_request_value.append(round(float(request[comparison_metric]) / 1000, 2))
            green_request_name.append(request['request_name'])
        if request[comparison_metric + '_threshold'] == 'orange':
            yellow_keys.append(count)
            count += 1
            yellow_request_value.append(round(-float(request[comparison_metric]) / 1000, 2))
            yellow_request_name.append(request['request_name'])
        if request[comparison_metric + '_threshold'] == 'red':
            red_keys.append(count)
            count += 1
            red_request_value.append(round(-float(request[comparison_metric]) / 1000, 2))
            red_request_name.append(request['request_name'])

    if green_keys.__len__() == 0:
        utility_key.append(count)
        count += 1
        utility_request_name.append('utility')
        if red_request_value.__len__() != 0:
            utility_request_value.append(-max(red_request_value)/2)
        else:
            utility_request_value.append(-max(yellow_request_value)/2)
    if yellow_keys.__len__() == 0 and red_keys.__len__() == 0:
        utility_key.append(count)
        count += 1
        utility_request_name.append('utility')
        utility_request_value.append(-max(green_request_value)/2)
    datapoints = {"green_keys": green_keys,
                  "yellow_keys": yellow_keys,
                  "red_keys": red_keys,
                  "utility_keys": utility_key,
                  "green_request": green_request_value,
                  "yellow_request": yellow_request_value,
                  "red_request": red_request_value,
                  "utility_request": utility_request_value,
                  "green_request_name": green_request_name,
                  "yellow_request_name": yellow_request_name,
                  "red_request_name": red_request_name,
                  "utility_request_name": utility_request_name,
                  'width': 8,
                  'height': 4.5,
                  "x_axis": "Requests", "y_axis": "Time, s", "title": "Comparison vs Thresholds",
                  "path_to_save": "tmp/thresholds.png"}
    barchart(datapoints)
    fp = open('tmp/thresholds.png', 'rb')
    image = MIMEImage(fp.read())
    image.add_header('Content-ID', '<thresholds>')
    fp.close()
    return image


def get_top_five_baseline(last_test_data, baseline, comparison_metric):
    excided_baseline = []
    for request in last_test_data:
        for baseline_request in baseline:
            if request['request_name'] == baseline_request['request_name']:
                if int(request[comparison_metric]) > int(baseline_request[comparison_metric]):
                    req = {}
                    if str(request['request_name']).__len__() > 25:
                        req['request_name'] = str(request['request_name'])[:25] + "...: "
                    else:
                        req['request_name'] = str(request['request_name']) + ": "
                    req['response_time'] = str(round(float(request[comparison_metric])/1000, 2)) + " sec"
                    req['delta'] = int(request[comparison_metric]) - int(baseline_request[comparison_metric])
                    excided_baseline.append(req)
    excided_baseline = sorted(excided_baseline, key=lambda k: k['delta'], reverse=True)
    if excided_baseline.__len__() > 5:
        return excided_baseline[:5]
    else:
        return excided_baseline


def get_top_five_thresholds(last_test_data, comparison_metric):
    excided_thresholds = []
    for request in last_test_data:
        if request[comparison_metric + '_threshold'] == 'orange':
            req = {}
            if str(request['request_name']).__len__() > 25:
                req['request_name'] = str(request['request_name'])[:25] + "...: "
            else:
                req['request_name'] = str(request['request_name']) + ": "
            req['response_time'] = str(round(float(request[comparison_metric]) / 1000, 2)) + " sec"
            req['delta'] = int(request[comparison_metric]) - int(request['yellow_threshold_value'])
            req['color'] = 'yellow'
            req['style_color'] = 'orange'
            excided_thresholds.append(req)
        if request[comparison_metric + '_threshold'] == 'red':
            req = {}
            if str(request['request_name']).__len__() > 25:
                req['request_name'] = str(request['request_name'])[:25] + "...: "
            else:
                req['request_name'] = str(request['request_name']) + ": "
            req['response_time'] = str(round(float(request[comparison_metric]) / 1000, 2)) + " sec"
            req['delta'] = int(request[comparison_metric]) - int(request['yellow_threshold_value'])
            req['color'] = 'red'
            req['style_color'] = 'red'
            excided_thresholds.append(req)
    excided_thresholds = sorted(excided_thresholds, key=lambda k: k['delta'], reverse=True)
    if excided_thresholds.__len__() > 5:
        return excided_thresholds[:5]
    else:
        return excided_thresholds


def create_tmp_folder():
    if not path.exists(path.join(getcwd(), 'tmp')):
        makedirs(path.join(getcwd(), 'tmp'))
    else:
        rmtree(path.join(getcwd(), 'tmp'), ignore_errors=True)
        makedirs(path.join(getcwd(), 'tmp'))
