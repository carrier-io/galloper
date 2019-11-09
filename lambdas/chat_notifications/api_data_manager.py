from influxdb import InfluxDBClient
import time
import calendar
import datetime


SELECT_LAST_BUILDS_ID = "select distinct(id) from (select build_id as id, pct95 from api_comparison where " \
                        "simulation=\'{}\' and test_type=\'{}\' and \"users\"=\'{}\' and build_id!~/audit_{}_/ " \
                        "order by time DESC) GROUP BY time(1s) order by DESC limit {}"

SELECT_BASELINE_BUILD_ID = "select last(pct95), build_id from api_comparison where simulation=\'{}\' and " \
                           "test_type=\'{}\' and \"users\"=\'{}\' and build_id=~/audit_{}_/"

SELECT_TEST_DATA = "select * from api_comparison where build_id=\'{}\'"

SELECT_THRESHOLDS = "select last(red) as red, last(yellow) as yellow from threshold where request_name=\'{}\' " \
                    "and simulation=\'{}\'"


class APIDataManager:

    def __init__(self, arguments):
        self.args = arguments
        self.client = InfluxDBClient(arguments['influx_host'], arguments['influx_port'],
                                     username=arguments['influx_user'], password=arguments['influx_password'])

    def prepare_api_test_data(self):
        tests_data = self.get_last_builds()
        if len(tests_data) == 0:
            raise Exception("No data found for given parameters")
        last_test_data = tests_data[0]
        last_test_data = self.append_api_thresholds_to_test_data(last_test_data)
        baseline = self.get_baseline()
        summary = self.create_api_test_summary(last_test_data, baseline, self.args['comparison_metric'])
        if baseline:
            previous_test = baseline
        elif len(tests_data) > 1:
            previous_test = tests_data[1]
        else:
            previous_test = None

        return summary, last_test_data, previous_test

    def get_last_builds(self):
        tests_data = []
        build_ids = []
        self.client.switch_database(self.args['influx_comparison_database'])
        last_builds = self.client.query(SELECT_LAST_BUILDS_ID.format(self.args['test'], self.args['test_type'],
                                                                     str(self.args['users']), self.args['test'],
                                                                     self.args['test_limit']))
        for test in list(last_builds.get_points()):
            if test['distinct'] not in build_ids:
                build_ids.append(test['distinct'])
        for _id in build_ids:
            test_data = self.client.query(SELECT_TEST_DATA.format(_id))
            tests_data.append(list(test_data.get_points()))
        return tests_data

    def append_api_thresholds_to_test_data(self, test):
        self.client.switch_database(self.args['influx_thresholds_database'])
        params = ['request_name', 'total', 'throughput', 'ko', 'min', 'max', 'pct50', 'pct75', 'pct95', 'time',
                  'simulation', 'users', 'duration']
        test_summary = []
        for request in test:
            request_data = {}
            comparison_metric = self.args['comparison_metric']
            threshold = self.client.query(SELECT_THRESHOLDS.format(str(request['request_name']),
                                                                   str(request['simulation'])))
            if len(list(threshold.get_points())) == 0:
                red_threshold = 3000
                yellow_threshold = 2000
            else:
                red_threshold = int(list(threshold.get_points())[0]['red'])
                yellow_threshold = int(list(threshold.get_points())[0]['yellow'])

            if int(request[comparison_metric]) < yellow_threshold:
                request_data[comparison_metric + '_threshold'] = 'green'
            else:
                request_data[comparison_metric + '_threshold'] = 'yellow'
            if int(request[comparison_metric]) >= red_threshold:
                request_data[comparison_metric + '_threshold'] = 'red'
            request_data['yellow_threshold_value'] = yellow_threshold
            request_data['red_threshold_value'] = red_threshold
            for param in params:
                request_data[param] = request[param]
            test_summary.append(request_data)
        return test_summary

    def get_baseline(self):
        self.client.switch_database(self.args['influx_comparison_database'])
        baseline_build_id = self.client.query(SELECT_BASELINE_BUILD_ID.format(self.args['test'], self.args['test_type'],
                                                                              str(self.args['users']),
                                                                              self.args['test']))
        result = list(baseline_build_id.get_points())
        if len(result) == 0:
            return None
        _id = result[0]['build_id']
        baseline_data = self.client.query(SELECT_TEST_DATA.format(_id))
        self.client.close()
        return list(baseline_data.get_points())

    def create_api_test_summary(self, test, baseline, comparison_metric):
        params = ['simulation', 'users', 'duration']
        test_params = {}
        for param in params:
            test_params[param] = test[0][param]
        test_params['end'] = str(test[0]['time']).replace("T", " ").replace("Z", "")
        timestamp = calendar.timegm(time.strptime(test_params['end'], '%Y-%m-%d %H:%M:%S'))
        test_params['start'] = datetime.datetime.utcfromtimestamp(int(timestamp) - int(float(test[0]['duration']))) \
            .strftime('%Y-%m-%d %H:%M:%S')
        test_params['status'], test_params['failed_reason'] = self.check_api_test_status(test,
                                                                                        baseline, comparison_metric)
        return test_params

    def check_api_test_status(self, test, baseline, comparison_metric):
        failed_reasons = []
        failed_message = self.check_api_test_functional_issues(test)
        if failed_message != '':
            failed_reasons.append(failed_message)
        failed_message = self.check_api_test_performance_degradation(test, baseline, comparison_metric)
        if failed_message != '':
            failed_reasons.append(failed_message)
        failed_message = self.check_api_test_missed_thresholds(test, comparison_metric)
        if failed_message != '':
            failed_reasons.append(failed_message)
        if failed_reasons:
            return 'FAILED', failed_reasons
        return 'SUCCESS', []

    @staticmethod
    def check_api_test_functional_issues(test):
        request_count, error_count = 0, 0
        for request in test:
            request_count += int(request['total'])
            error_count += int(request['ko'])
        error_rate = round(error_count * 100 / request_count, 2)
        if error_rate > 10:
            return 'error rate - ' + str(error_rate) + ' %'
        return ''

    @staticmethod
    def check_api_test_performance_degradation(test, baseline, comparison_metric):
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
                return 'performance degradation rate - ' + str(performance_degradation_rate) + ' %'
            else:
                return ''
        else:
            return ''

    @staticmethod
    def check_api_test_missed_thresholds(test, comparison_metric):
        request_count, missed_thresholds = 0, 0
        for request in test:
            request_count += 1
            if request[comparison_metric + '_threshold'] is not 'green':
                missed_thresholds += 1
        missed_thresholds_rate = round(missed_thresholds * 100 / request_count, 2)
        if missed_thresholds_rate > 50:
            return 'missed thresholds rate - ' + str(missed_thresholds_rate) + ' %'
        return ''
