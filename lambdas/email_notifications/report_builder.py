import time
import calendar
import datetime
from chart_generator import *
from email.mime.image import MIMEImage


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


def create_ui_test_discription(test):
    description = {}
    description['start_time'] = datetime.datetime.utcfromtimestamp(int(test[0]['start_time'])/1000)\
        .strftime('%Y-%m-%d %H:%M:%S')
    description['scenario'] = test[0]['scenario']
    description['suite'] = test[0]['suite']
    count = 0
    errors = 0
    for page in test:
        count += int(page['count'])
        errors += int(page['failed'])
    error_rate = errors * 1000 / count
    failed_reasons = []
    if error_rate > 10:
        description['status'] = 'FAILED'
        failed_reasons.append('error rate - ' + str(error_rate) + ' %')
    else:
        description['status'] = 'SUCCESS'
    page_count = 0
    missed_thresholds = 0
    for page in test:
        page_count += 1
        if page['time_threshold'] != 'green':
            missed_thresholds += 1
    missed_thresholds_rate = round(missed_thresholds * 100 / page_count, 2)
    if missed_thresholds_rate > 50:
        description['status'] = 'FAILED'
        failed_reasons.append('missed thresholds - ' + str(missed_thresholds_rate) + ' %')
    if description['status'] is 'SUCCESS':
        description['color'] = 'green'
    else:
        description['color'] = 'red'
    description['failed_reason'] = failed_reasons
    return description


def check_status(test, baseline, comparison_metric):
    failed_reasons = []
    test_status, failed_message = check_functional_issues(test)
    if failed_message != '':
        failed_reasons.append(failed_message)
    status, failed_message = check_performance_degradation(test, baseline, comparison_metric)
    if failed_message != '':
        failed_reasons.append(failed_message)
    if test_status is 'SUCCESS':
        test_status = status
    status, failed_message = check_missed_thresholds(test, comparison_metric)
    if failed_message != '':
        failed_reasons.append(failed_message)
    if test_status is 'SUCCESS':
        test_status = status
    if test_status is 'SUCCESS':
        color = 'green'
    else:
        color = 'red'
    return status, color, failed_reasons


def check_functional_issues(test):
    request_count = 0
    error_count = 0
    for request in test:
        request_count += int(request['total'])
        error_count += int(request['ko'])
    error_rate = round(error_count * 100 / request_count, 2)
    if error_rate > 10:
        return 'FAILED', 'error rate - ' + str(error_rate) + ' %'
    return 'SUCCESS', ''


def check_performance_degradation(test, baseline, comparison_metric):
    if baseline:
        request_count = 0
        performance_degradation = 0
        for request in test:
            request_count += 1
            for baseline_request in baseline:
                if request['request_name'] == baseline_request['request_name']:
                    if int(request[comparison_metric]) > int(baseline_request[comparison_metric]):
                        performance_degradation += 1
        performance_degradation_rate = round(performance_degradation * 100 / request_count, 2)
        if performance_degradation_rate > 20:
            return 'FAILED', 'performance degradation rate - ' + str(performance_degradation_rate) + ' %'
        else:
            return 'SUCCESS', ''
    else:
        return 'SUCCESS', ''


def check_missed_thresholds(test, comparison_metric):
    request_count = 0
    missed_thresholds = 0
    for request in test:
        request_count += 1
        if request[comparison_metric + '_threshold'] is not 'green':
            missed_thresholds += 1
    missed_thresholds_rate = round(missed_thresholds * 100 / request_count, 2)
    if missed_thresholds_rate > 1:
        return 'FAILED', 'missed thresholds rate - ' + str(missed_thresholds_rate) + ' %'
    return 'SUCCESS', ''


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
        test_info['pct95'] = round(pct95 / request_count, 2)
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
    build_info['error_rate_diff'] = round(float(build['error_rate']) - float(last_build['error_rate']), 2)
    if build_info['error_rate_diff'] > 0.0:
        build_info['error_rate_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['error_rate_diff'])
    else:
        build_info['error_rate_diff'] = str(build_info['error_rate_diff']
                                            ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    build_info['pct95_diff'] = round(float(build['pct95']) * 100 /
                                     float(last_build['pct95']) - 100, 1)
    if build_info['pct95_diff'] > 0.0:
        build_info['pct95_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['pct95_diff'])
    else:
        build_info['pct95_diff'] = str(build_info['pct95_diff']
                                       ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    build_info['total_diff'] = round(float(build['total']) * 100 / float(last_build['total']) - 100, 1)
    if build_info['total_diff'] > 0.0:
        build_info['total_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['total_diff'])
    else:
        build_info['total_diff'] = str(build_info['total_diff']
                                       ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    if float(last_build['throughput']) != 0.0:
        build_info['throughput_diff'] = round(float(build['throughput']
                                                    ) * 100 / float(last_build['throughput']) - 100, 1)
    else:
        build_info['throughput_diff'] = 0.0
    if build_info['throughput_diff'] > 0.0:
        build_info['throughput_diff'] = "<b style=\"color: red\">&#9650;</b>" + \
                                        str(build_info['throughput_diff'])
    else:
        build_info['throughput_diff'] = str(build_info['throughput_diff']
                                            ).replace("-", "<b style=\"color: green\">&#9660;</b>")

    for param in params:
        build_info[param] = build[param]
    return build_info


def create_charts(builds, last_test_data, baseline, comparison_metric):
    charts = []
    if builds.__len__() > 1:
        charts.append(create_success_rate_chart(builds))
    if builds.__len__() > 1:
        charts.append(create_throughput_chart(builds))
    if baseline:
        charts.append(create_comparison_vs_baseline_barchart(last_test_data, baseline, comparison_metric))
    charts.append(create_thresholds_chart(last_test_data, comparison_metric))
    return charts


def create_success_rate_chart(builds):
    labels = []
    keys = []
    values = []
    count = 1
    for test in builds:
        labels.append(test['date'])
        keys.append(round(100 - test['error_rate'], 2))
        values.append(count)
        count += 1
    datapoints = {
        'title': 'Successful requests, %',
        'label': 'Successful requests, %',
        'x_axis': 'Test Runs',
        'y_axis': 'Successful requests, %',
        'width': 10,
        'height': 3,
        'path_to_save': '/tmp/success_rate.png',
        'keys': keys[::-1],
        'values': values,
        'labels': labels[::-1]
    }
    alerts_linechart(datapoints)
    fp = open('/tmp/success_rate.png', 'rb')
    image = MIMEImage(fp.read())
    image.add_header('Content-ID', '<success_rate>')
    fp.close()
    return image


def create_throughput_chart(builds):
    labels = []
    keys = []
    values = []
    count = 1
    for test in builds:
        labels.append(test['date'])
        keys.append(test['throughput'])
        values.append(count)
        count += 1
    datapoints = {
        'title': 'Throughput',
        'label': 'Throughput, req/s',
        'x_axis': 'Test Runs',
        'y_axis': 'Throughput, req/s',
        'width': 10,
        'height': 3,
        'path_to_save': '/tmp/throughput.png',
        'keys': keys[::-1],
        'values': values,
        'labels': labels[::-1]
    }
    alerts_linechart(datapoints)
    fp = open('/tmp/throughput.png', 'rb')
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
                  "path_to_save": "/tmp/baseline.png"}
    barchart(datapoints)
    fp = open('/tmp/baseline.png', 'rb')
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
                  "path_to_save": "/tmp/thresholds.png"}
    barchart(datapoints)
    fp = open('/tmp/thresholds.png', 'rb')
    image = MIMEImage(fp.read())
    image.add_header('Content-ID', '<thresholds>')
    fp.close()
    return image


def create_ui_charts(test, builds_comparison):
    charts = []
    charts.append(create_thresholds_chart(test, 'time'))
    if builds_comparison.__len__() > 1:
        charts.append(create_comparison_chart(builds_comparison))
    if builds_comparison.__len__() > 1:
        charts.append(create_success_rate_chart(builds_comparison))
    return charts


def create_comparison_chart(builds_comparison):
    labels = []
    keys = []
    latency_values = []
    transfer_values = []
    tti_values = []
    ttl_values = []
    total_time_values = []
    count = 1
    for build in builds_comparison:
        labels.append(build['date'])
        keys.append(count)
        count += 1
        latency_values.append(build['latency'])
        transfer_values.append(build['transfer'])
        tti_values.append(build['tti'])
        ttl_values.append(build['ttl'])
        total_time_values.append(build['total_time'])
    datapoints = {
        'title': '',
        'label': 'Time, sec',
        'x_axis': 'Test Runs',
        'y_axis': 'Time, sec',
        'width': 10,
        'height': 3,
        'path_to_save': '/tmp/comparison.png',
        'keys': keys,
        'latency_values': latency_values[::-1],
        'transfer_values': transfer_values[::-1],
        'tti_values': tti_values[::-1],
        'ttl_values': ttl_values[::-1],
        'total_time_values': total_time_values[::-1],
        'labels': labels[::-1]
    }
    ui_comparison_linechart(datapoints)
    fp = open('/tmp/comparison.png', 'rb')
    image = MIMEImage(fp.read())
    image.add_header('Content-ID', '<comparison>')
    fp.close()
    return image


def get_top_five_baseline(last_test_data, baseline, comparison_metric):
    if baseline:
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
    else:
        return []


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


def aggregate_results(tests):
    tests_data = []
    for test in tests:
        test_data = {}
        for page in list(test.get_points()):
            if page['page'] not in test_data:
                test_data[page['page']] = {
                    'scenario': page['scenario'],
                    'suite': page['suite'],
                    'build_id': page['build_id'],
                    'start_time': page['start_time'],
                    'request_name': page['page'],
                    'url': str(page['domain']) + str(page['url']),
                    'count': 1,
                    'failed': 0,
                    'total_time': [page['total_time']],
                    'ttl': [page['ttl']],
                    'tti': [page['tti']],
                    'onload': [page['onload']],
                    'latency': [page['latency']],
                    'transfer': [page['transfer']],
                    'encodedBodySize': page['encodedBodySize'],
                    'decodedBodySize': page['decodedBodySize']
                }
                if page['status'] == 'ko':
                    test_data[page['page']]['failed'] = int(test_data[page['page']]['failed']) + 1
            else:
                test_data[page['page']]['total_time'].append(page['total_time'])
                test_data[page['page']]['ttl'].append(page['ttl'])
                test_data[page['page']]['tti'].append(page['tti'])
                test_data[page['page']]['onload'].append(page['onload'])
                test_data[page['page']]['latency'].append(page['latency'])
                test_data[page['page']]['transfer'].append(page['transfer'])
                test_data[page['page']]['count'] = int(test_data[page['page']]['count']) + 1
                if page['status'] == 'ko':
                    test_data[page['page']]['failed'] = int(test_data[page['page']]['failed']) + 1
        tests_data.append(list(test_data.values()))
    return tests_data


def create_ui_builds_comparison(tests):
    comparison = []
    builds_info = []
    for build in tests:
        build_info = {}
        page_count = 0
        error_count = 0
        for page in build:
            page_count += page['count']
            error_count += page['failed']
            build_info['ttl'] = round(median(page['ttl'])/1000.0, 2)
            build_info['tti'] = round(median(page['tti'])/1000.0, 2)
            build_info['transfer'] = round(median(page['transfer'])/1000.0, 2)
            build_info['latency'] = round(median(page['latency'])/1000.0, 2)
            build_info['total_time'] = round(median(page['total_time'])/1000.0, 2)
        build_info['date'] = datetime.datetime.utcfromtimestamp(int(build[0]['start_time']) / 1000) \
            .strftime('%d-%b %H:%M')
        build_info['count'] = page_count
        build_info['error_rate'] = round((error_count / page_count) * 100, 2)
        builds_info.append(build_info)
    last_build = builds_info[0]
    for build in builds_info:
        comparison.append(compare_ui_builds(last_build, build))
    return comparison


def compare_ui_builds(last_build, build):
    build_info = {}
    params = ['date', 'error_rate', 'ttl', 'tti', 'transfer', 'latency', 'total_time', 'count']
    build_info['error_rate_diff'] = float(build['error_rate']) - float(last_build['error_rate'])
    if build_info['error_rate_diff'] > 0.0:
        build_info['error_rate_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['error_rate_diff'])
    else:
        build_info['error_rate_diff'] = str(build_info['error_rate_diff']
                                            ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    build_info['total_page_diff'] = round(float(build['count']) * 100 / float(last_build['count']) - 100, 1)
    if build_info['total_page_diff'] > 0.0:
        build_info['total_page_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['total_page_diff'])
    else:
        build_info['total_page_diff'] = str(build_info['total_page_diff']
                                            ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    build_info['total_ttl_diff'] = round(float(build['ttl']) * 100 / float(last_build['ttl']) - 100, 1)
    if build_info['total_ttl_diff'] > 0.0:
        build_info['total_ttl_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['total_ttl_diff'])
    else:
        build_info['total_ttl_diff'] = str(build_info['total_ttl_diff']
                                           ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    build_info['total_tti_diff'] = round(float(build['tti']) * 100 / float(last_build['tti']) - 100, 1)
    if build_info['total_tti_diff'] > 0.0:
        build_info['total_tti_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['total_tti_diff'])
    else:
        build_info['total_tti_diff'] = str(build_info['total_tti_diff']
                                           ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    build_info['total_transfer_diff'] = round(float(build['transfer']) * 100 / float(last_build['transfer']) - 100, 1)
    if build_info['total_transfer_diff'] > 0.0:
        build_info['total_transfer_diff'] = "<b style=\"color: red\">&#9650;</b>" + \
                                            str(build_info['total_transfer_diff'])
    else:
        build_info['total_transfer_diff'] = str(build_info['total_transfer_diff']
                                                ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    build_info['total_latency_diff'] = round(float(build['latency']) * 100 / float(last_build['latency']) - 100, 1)
    if build_info['total_latency_diff'] > 0.0:
        build_info['total_latency_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['total_latency_diff'])
    else:
        build_info['total_latency_diff'] = str(build_info['total_latency_diff']
                                               ).replace("-", "<b style=\"color: green\">&#9660;</b>")
    build_info['total_time_diff'] = round(float(build['total_time']) * 100 / float(last_build['total_time']) - 100, 1)
    if build_info['total_time_diff'] > 0.0:
        build_info['total_time_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['total_time_diff'])
    else:
        build_info['total_time_diff'] = str(build_info['total_time_diff']
                                            ).replace("-", "<b style=\"color: green\">&#9660;</b>")

    for param in params:
        build_info[param] = build[param]
    return build_info


def aggregate_last_test_results(test):
    test_data = []
    params = ['request_name', 'count', 'failed', 'time_threshold']
    for page in test:
        page_info = {}
        for param in params:
            page_info[param] = page[param]
        page_info['ttl'] = round(median(page['ttl']) / 1000.0, 2)
        page_info['tti'] = round(median(page['tti']) / 1000.0, 2)
        page_info['transfer'] = round(median(page['transfer']) / 1000.0, 2)
        page_info['latency'] = round(median(page['latency']) / 1000.0, 2)
        page_info['total_time'] = round(median(page['total_time']) / 1000.0, 2)
        test_data.append(page_info)
    return test_data


def median(lst):
    n = len(lst)
    if n < 1:
        return None
    if n % 2 == 1:
        return sorted(lst)[n // 2]
    else:
        return sum(sorted(lst)[n // 2 - 1:n // 2 + 1]) / 2.0
