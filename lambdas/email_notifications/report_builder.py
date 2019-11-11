import time
import calendar
import datetime
from chart_generator import *
from email.mime.image import MIMEImage
import statistics
from jinja2 import Environment, FileSystemLoader

GREEN = '#028003'
YELLOW = '#FFA400'
RED = '#FF0000'

class ReportBuilder:

    def create_api_email_body(self, tests_data, last_test_data, baseline, comparison_metric):
        test_description = self.create_test_description(last_test_data, baseline, comparison_metric)
        builds_comparison = self.create_builds_comparison(tests_data)
        general_metrics = self.get_general_metrics(builds_comparison[0], baseline, {})
        charts = self.create_charts(builds_comparison, last_test_data, baseline, comparison_metric)
        baseline_and_thresholds = self.get_baseline_and_thresholds(last_test_data, baseline, comparison_metric)
        email_body = self.get_api_email_body(test_description, last_test_data, baseline, builds_comparison,
                                             baseline_and_thresholds, general_metrics)
        return email_body, charts, str(test_description['start']).split(" ")[0]

    def create_ui_email_body(self, tests_data, last_test_data):
        test_params = self.create_ui_test_discription(last_test_data)
        top_five_thresholds = self.get_baseline_and_thresholds(last_test_data, None, 'time')
        builds_comparison = self.create_ui_builds_comparison(tests_data)
        charts = self.create_ui_charts(last_test_data, builds_comparison)
        last_test_data = self.aggregate_last_test_results(last_test_data)
        email_body = self.get_ui_email_body(test_params, top_five_thresholds, builds_comparison, last_test_data)
        return email_body, charts, str(test_params['start_time']).split(" ")[0]

    def create_test_description(self, test, baseline, comparison_metric):
        params = ['simulation', 'users', 'duration']
        test_params = {}
        for param in params:
            test_params[param] = test[0][param]
        test_params['end'] = str(test[0]['time']).replace("T", " ").replace("Z", "")
        timestamp = calendar.timegm(time.strptime(test_params['end'], '%Y-%m-%d %H:%M:%S'))
        test_params['start'] = datetime.datetime.utcfromtimestamp(int(timestamp) - int(float(test[0]['duration']))) \
            .strftime('%Y-%m-%d %H:%M:%S')
        test_params['status'], test_params['color'], test_params['failed_reason'] = self.check_status(test, baseline,
                                                                                                      comparison_metric)
        return test_params
        
    @staticmethod
    def create_ui_test_discription(test):
        description = {'start_time': datetime.datetime.utcfromtimestamp(int(test[0]['start_time']) / 1000).strftime(
            '%Y-%m-%d %H:%M:%S'), 'scenario': test[0]['scenario'], 'suite': test[0]['suite']}
        count, errors = 0, 0
        for page in test:
            count += int(page['count'])
            errors += int(page['failed'])
        error_rate = round(errors * 100 / count, 2)
        failed_reasons = []
        if error_rate > 10:
            description['status'] = 'FAILED'
            failed_reasons.append('error rate - ' + str(error_rate) + ' %')
        else:
            description['status'] = 'SUCCESS'
        page_count, missed_thresholds = 0, 0
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

    def check_status(self, test, baseline, comparison_metric):
        failed_reasons = []
        test_status, failed_message = self.check_functional_issues(test)
        if failed_message != '':
            failed_reasons.append(failed_message)
        status, failed_message = self.check_performance_degradation(test, baseline, comparison_metric)
        if failed_message != '':
            failed_reasons.append(failed_message)
        if test_status is 'SUCCESS':
            test_status = status
        status, failed_message = self.check_missed_thresholds(test, comparison_metric)
        if failed_message != '':
            failed_reasons.append(failed_message)
        if test_status is 'SUCCESS':
            test_status = status
        if test_status is 'SUCCESS':
            color = GREEN
        else:
            color = RED
        return status, color, failed_reasons

    @staticmethod
    def check_functional_issues(test):
        request_count, error_count = 0, 0
        for request in test:
            request_count += int(request['total'])
            error_count += int(request['ko'])
        error_rate = round(error_count * 100 / request_count, 2)
        if error_rate > 10:
            return 'FAILED', 'error rate - ' + str(error_rate) + ' %'
        return 'SUCCESS', ''

    @staticmethod
    def check_performance_degradation(test, baseline, comparison_metric):
        if baseline:
            request_count, performance_degradation = 0, 0
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

    @staticmethod
    def check_missed_thresholds(test, comparison_metric):
        request_count, missed_thresholds = 0, 0
        for request in test:
            request_count += 1
            if request[comparison_metric + '_threshold'] is not 'green':
                missed_thresholds += 1
        missed_thresholds_rate = round(missed_thresholds * 100 / request_count, 2)
        if missed_thresholds_rate > 50:
            return 'FAILED', 'missed thresholds rate - ' + str(missed_thresholds_rate) + ' %'
        return 'SUCCESS', ''

    def create_builds_comparison(self, tests):
        builds_comparison = []
        for test in tests:
            test_info = {}
            request_count, total_request_count, avg_throughput, error_count, pct95 = 0, 0, 0, 0, 0
            for request in test:
                request_count += 1
                total_request_count += int(request['total'])
                avg_throughput += float(request['throughput'])
                error_count += float(request['ko'])
                pct95 += int(request['pct95'])
            date = str(test[0]['time']).replace("T", " ").replace("Z", "")
            timestamp = calendar.timegm(time.strptime(date, '%Y-%m-%d %H:%M:%S'))
            test_info['date'] = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%d-%b %H:%M')
            test_info['total'] = total_request_count
            test_info['throughput'] = round(avg_throughput, 2)
            test_info['pct95'] = round(pct95 / request_count, 2)
            test_info['error_rate'] = round((error_count / total_request_count) * 100, 2)
            builds_comparison.append(test_info)
        builds_comparison = self.calculate_diffs(builds_comparison)

        return builds_comparison

    def calculate_diffs(self, builds):
        builds_comparison = []
        last_build = builds[0]
        for build in builds:
            build_info_with_diffs = self.compare_builds(build, last_build)
            builds_comparison.append(build_info_with_diffs)
        return builds_comparison

    @staticmethod
    def compare_builds(build, last_build):
        build_info = {}
        for param in ['date', 'error_rate', 'pct95', 'total', 'throughput']:
            param_diff = None
            if param in ['error_rate']:
                param_diff = round(float(build[param]) - float(last_build.get(param, 0.0)), 2)
                color = RED if param_diff > 0.0 else GREEN
            if param in ['throughput', 'total']:
                param_diff = round(float(build[param]) - float(last_build.get(param, 0.0)), 2)
                color = RED if param_diff < 0.0 else GREEN
            if param in ['pct95']:
                param_diff = round((float(build[param]) - float(last_build[param]))/1000, 2)
                color = RED if param_diff > 0.0 else GREEN
            if param_diff is not None:
                param_diff = f"+{param_diff}" if param_diff > 0 else str(param_diff)
                build_info[f'{param}_diff'] = f"<p style=\"color: {color}\">{param_diff}</p>"
            build_info[param] = build[param]
        return build_info

    def create_charts(self, builds, last_test_data, baseline, comparison_metric):
        charts = []
        if len(builds) > 1:
            charts.append(self.create_success_rate_chart(builds))
            charts.append(self.create_throughput_chart(builds))
        return charts

    @staticmethod
    def create_success_rate_chart(builds):
        labels, keys, values = [], [], []
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

    @staticmethod
    def create_throughput_chart(builds):
        labels, keys, values = [], [], []
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

    @staticmethod
    def create_comparison_vs_baseline_barchart(last_test_data, baseline, comparison_metric):
        green_keys, yellow_keys, utility_key, green_request_value, yellow_request_value = [], [], [], [], []
        utility_request_value, green_request_name, yellow_request_name, utility_request_name = [], [], [], []
        count = 1
        for request in last_test_data:
            for baseline_request in baseline:
                if request['request_name'] == baseline_request['request_name']:
                    if int(request[comparison_metric]) > int(baseline_request[comparison_metric]):
                        yellow_keys.append(count)
                        count += 1
                        yellow_request_value.append(round(-float(request[comparison_metric]) / 1000, 2))
                        yellow_request_name.append(request['request_name'])
                    else:
                        green_keys.append(count)
                        count += 1
                        green_request_value.append(round(float(request[comparison_metric]) / 1000, 2))
                        green_request_name.append(request['request_name'])

        if len(green_keys) == 0:
            utility_key.append(count)
            count += 1
            utility_request_name.append('utility')
            utility_request_value.append(-max(yellow_request_value) / 2)
        if len(yellow_keys) == 0:
            utility_key.append(count)
            count += 1
            utility_request_name.append('utility')
            utility_request_value.append(-max(green_request_value) / 2)
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

    @staticmethod
    def create_thresholds_chart(last_test_data, comparison_metric):
        green_keys, yellow_keys, red_keys, utility_key, green_request_value = [], [], [], [], []
        yellow_request_value, red_request_value, utility_request_value, green_request_name = [], [], [], []
        yellow_request_name, red_request_name, utility_request_name = [], [], []
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

        if len(green_keys) == 0:
            utility_key.append(count)
            count += 1
            utility_request_name.append('utility')
            if len(red_request_value) != 0:
                utility_request_value.append(-max(red_request_value) / 2)
            else:
                utility_request_value.append(-max(yellow_request_value) / 2)
        if len(yellow_keys) == 0 and len(red_keys) == 0:
            utility_key.append(count)
            count += 1
            utility_request_name.append('utility')
            utility_request_value.append(-max(green_request_value) / 2)
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

    def create_ui_charts(self, test, builds_comparison):
        charts = [self.create_thresholds_chart(test, 'time')]
        if len(builds_comparison) > 1:
            charts.append(self.create_comparison_chart(builds_comparison))
        if len(builds_comparison) > 1:
            charts.append(self.create_success_rate_chart(builds_comparison))
        return charts

    @staticmethod
    def create_comparison_chart(builds_comparison):
        labels, keys, latency_values, transfer_values = [], [], [], []
        tti_values, ttl_values, total_time_values = [], [], []
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

    @staticmethod
    def get_general_metrics(build_data, baseline, thresholds=None):
        current_tp = build_data['throughput']
        current_error_rate = build_data['error_rate']
        baseline_throughput = 0
        baseline_error_rate = 0
        if baseline:
            baseline_throughput = round(sum([tp['throughput'] for tp in baseline]), 2)
            baseline_ko_count = round(sum([tp['ko'] for tp in baseline]), 2)
            baseline_ok_count = round(sum([tp['ok'] for tp in baseline]), 2)
            baseline_error_rate = round((baseline_ko_count / (baseline_ko_count+baseline_ok_count)) * 100, 2)
        baseline_tp_color = RED if baseline_throughput > current_tp else GREEN
        baseline_er_color = RED if current_error_rate > baseline_error_rate else GREEN
        thresholds_tp_color = RED if thresholds.get('throughput', 0) > current_tp else GREEN
        thresholds_er_color = RED if current_error_rate > thresholds.get('error_rate', 0) else GREEN
        return {
            "current_tp": current_tp,
            "baseline_tp": round(current_tp - baseline_throughput, 2),
            "baseline_tp_color": baseline_tp_color,
            "threshold_tp": round(current_tp - thresholds.get('throughput', 0), 2),
            "threshold_tp_color": thresholds_tp_color,
            "current_er": current_error_rate,
            "baseline_er": round(current_error_rate - baseline_error_rate, 2),
            "baseline_er_color": baseline_er_color,
            "threshold_er": round(current_error_rate - thresholds.get('error_rate', 0), 2),
            "threshold_er_color": thresholds_er_color
        }

    @staticmethod
    def get_baseline_and_thresholds(last_test_data, baseline, comparison_metric):
        exceeded_thresholds = []
        baseline_metrics = {}
        if baseline:
            for request in baseline:
                baseline_metrics[request['request_name']] = int(request[comparison_metric])
        for request in last_test_data:
            req = {}
            req['response_time'] = str(round(float(request[comparison_metric]) / 1000, 2))
            req['threshold_value'] = str(request['yellow_threshold_value'])
            req['threshold'] = round(float(int(request[comparison_metric]) - int(request['yellow_threshold_value']))/ 1000, 2)
            if len(str(request['request_name'])) > 25:
                req['request_name'] = str(request['request_name'])[:25] + "... "
            else:
                req['request_name'] = str(request['request_name'])
            if request[comparison_metric + '_threshold'] == YELLOW:
                req['threshold_color'] = YELLOW
            elif request[comparison_metric + '_threshold'] == RED:
                req['threshold_value'] = str(request['red_threshold_value'])
                req['threshold'] = round(float(int(request[comparison_metric]) - int(request['red_threshold_value']))/ 1000, 2)
                req['threshold_color'] = RED
            else:
                req['threshold_color'] = GREEN
            if baseline:
                req['baseline'] = round(float(int(request[comparison_metric]) - baseline_metrics[request['request_name']]) / 1000, 2)
                if req['baseline'] < 0:
                    req['baseline_color'] = GREEN
                else:
                    req['baseline_color'] = YELLOW
            if req['threshold_color'] == RED:
                req['line_color'] = RED
            elif req['threshold_color'] == GREEN and req.get('baseline_color', GREEN) == GREEN:
                req['line_color'] = GREEN
            else:
                req['line_color'] = YELLOW
            exceeded_thresholds.append(req)
        exceeded_thresholds = sorted(exceeded_thresholds, key=lambda k: k['response_time'], reverse=True)
        hundered = 0
        for _ in range(len(exceeded_thresholds)):
            if not(hundered):
                exceeded_thresholds[_]['share'] = 100
                hundered = float(exceeded_thresholds[_]['response_time'])
            else:
                exceeded_thresholds[_]['share'] = int((100*float(exceeded_thresholds[_]['response_time']))/hundered)
        return exceeded_thresholds

    def create_ui_builds_comparison(self, tests):
        comparison, builds_info = [], []
        for build in tests:
            build_info = {'ttl': [], 'tti': [], 'transfer': [], 'latency': [], 'total_time': []}
            page_count = 0
            error_count = 0
            for page in build:
                page_count += page['count']
                error_count += page['failed']
                build_info['ttl'].append(round(statistics.median(page['ttl']) / 1000.0, 2))
                build_info['tti'].append(round(statistics.median(page['tti']) / 1000.0, 2))
                build_info['transfer'].append(round(statistics.median(page['transfer']) / 1000.0, 2))
                build_info['latency'].append(round(statistics.median(page['latency']) / 1000.0, 2))
                build_info['total_time'].append(round(statistics.median(page['total_time']) / 1000.0, 2))
            build_info['ttl'] = statistics.median(build_info['ttl'])
            build_info['tti'] = statistics.median(build_info['tti'])
            build_info['transfer'] = statistics.median(build_info['transfer'])
            build_info['latency'] = statistics.median(build_info['latency'])
            build_info['total_time'] = statistics.median(build_info['total_time'])
            build_info['date'] = datetime.datetime.utcfromtimestamp(int(build[0]['start_time']) / 1000) \
                .strftime('%d-%b %H:%M')
            build_info['count'] = page_count
            build_info['error_rate'] = round((error_count / page_count) * 100, 2)
            builds_info.append(build_info)
        last_build = builds_info[0]
        for build in builds_info:
            comparison.append(self.compare_ui_builds(last_build, build))
        return comparison

    @staticmethod
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

        build_info['total_transfer_diff'] = round(float(build['transfer']) * 100 / float(last_build['transfer']) - 100,
                                                  1) if int(last_build['transfer']) != 0 else 0

        if build_info['total_transfer_diff'] > 0.0:
            build_info['total_transfer_diff'] = "<b style=\"color: red\">&#9650;</b>" + \
                                                str(build_info['total_transfer_diff'])
        else:
            build_info['total_transfer_diff'] = str(build_info['total_transfer_diff']
                                                    ).replace("-", "<b style=\"color: green\">&#9660;</b>")
        build_info['total_latency_diff'] = round(float(build['latency']) * 100 / float(last_build['latency']) - 100, 1)
        if build_info['total_latency_diff'] > 0.0:
            build_info['total_latency_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(
                build_info['total_latency_diff'])
        else:
            build_info['total_latency_diff'] = str(round(float(build_info['total_latency_diff']), 1)
                                                   ).replace("-", "<b style=\"color: green\">&#9660;</b>")
        build_info['total_time_diff'] = round(float(build['total_time']) * 100 / float(last_build['total_time']) - 100,
                                              1)
        if build_info['total_time_diff'] > 0.0:
            build_info['total_time_diff'] = "<b style=\"color: red\">&#9650;</b>" + str(build_info['total_time_diff'])
        else:
            build_info['total_time_diff'] = str(build_info['total_time_diff']
                                                ).replace("-", "<b style=\"color: green\">&#9660;</b>")

        for param in params:
            build_info[param] = build[param]
        return build_info

    @staticmethod
    def aggregate_last_test_results(test):
        test_data = []
        params = ['request_name', 'count', 'failed', 'time_threshold']
        for page in test:
            page_info = {}
            for param in params:
                page_info[param] = page[param]
            page_info['ttl'] = round(statistics.median(page['ttl']) / 1000.0, 2)
            page_info['tti'] = round(statistics.median(page['tti']) / 1000.0, 2)
            page_info['transfer'] = round(statistics.median(page['transfer']) / 1000.0, 2)
            page_info['latency'] = round(statistics.median(page['latency']) / 1000.0, 2)
            page_info['total_time'] = round(statistics.median(page['total_time']) / 1000.0, 2)
            test_data.append(page_info)
        return test_data

    @staticmethod
    def get_api_email_body(test_params, last_test_data, baseline, builds_comparison, baseline_and_thresholds, general_metrics):
        env = Environment(loader=FileSystemLoader('./templates/'))
        template = env.get_template("backend_email.html")
        html = template.render(t_params=test_params, summary=last_test_data, baseline=baseline,
                               comparison=builds_comparison,
                               baseline_and_thresholds=baseline_and_thresholds, general_metrics=general_metrics)
        return html

    @staticmethod
    def get_ui_email_body(test_params, top_five_thresholds, builds_comparison, last_test_data):
        env = Environment(loader=FileSystemLoader('./templates/'))
        template = env.get_template("ui_email_template.html")
        html = template.render(t_params=test_params, top_five_thresholds=top_five_thresholds,
                               comparison=builds_comparison,
                               summary=last_test_data)
        return html
