from influxdb import InfluxDBClient
import statistics


SELECT_LAST_BUILDS_ID = "select distinct(id) from (select build_id as id, pct95 from api_comparison where " \
                        "simulation=\'{}\' and test_type=\'{}\' and \"users\"=\'{}\' " \
                        "and build_id!~/audit_{}_/ order by time DESC) GROUP BY time(1s) order by DESC limit {}"

SELECT_TEST_DATA = "select * from api_comparison where build_id=\'{}\'"

SELECT_BASELINE_BUILD_ID = "select last(pct95), build_id from api_comparison where simulation=\'{}\' " \
                           "and test_type=\'{}\' and \"users\"=\'{}\' and build_id=~/audit_{}_/"

SELECT_THRESHOLDS = "select last(red) as red, last(yellow) as yellow from threshold where request_name=\'{}\' " \
                    "and simulation=\'{}\'"

SELECT_LAST_UI_BUILD_ID = "select distinct(id) from (select build_id as id, count from uiperf where scenario=\'{}\' " \
                          "and suite=\'{}\' group by start_time order by time DESC limit 1) GROUP BY time(1s) " \
                          "order by DESC limit {}"

SELECT_UI_TEST_DATA = "select build_id, scenario, suite, domain, start_time, page, status, url, latency, tti, ttl," \
                      " onload, total_time, transfer, firstPaint, encodedBodySize, decodedBodySize from uiperf " \
                      "where build_id=\'{}\'"


class DataManager:
    def __init__(self, arguments):
        self.args = arguments
        self.client = InfluxDBClient(arguments['influx_host'], arguments['influx_port'],
                                     username=arguments['influx_user'], password=arguments['influx_password'])

    def get_api_test_info(self):
        tests_data = self.get_last_builds()
        if len(tests_data) == 0:
            raise Exception("No data found for given parameters")
        last_test_data = tests_data[0]
        last_test_data = self.append_thresholds_to_test_data(last_test_data)
        baseline = self.get_baseline()
        return tests_data, last_test_data, baseline

    def get_ui_test_info(self):
        tests_data = self.get_ui_last_builds()
        if len(tests_data) == 0:
            raise Exception("No data found for given parameters")
        tests_data = self.aggregate_ui_test_results(tests_data)
        last_test_data = tests_data[0]
        last_test_data = self.append_ui_thresholds_to_test_data(last_test_data)
        return tests_data, last_test_data

    def get_last_builds(self):
        self.client.switch_database(self.args['influx_comparison_database'])
        tests_data = []
        build_ids = []
        last_builds = self.client.query(SELECT_LAST_BUILDS_ID.format(self.args['test'], self.args['test_type'],
                                                                     str(self.args['users']), self.args['test'],
                                                                     str(self.args['test_limit'])))
        for test in list(last_builds.get_points()):
            if test['distinct'] not in build_ids:
                build_ids.append(test['distinct'])

        for _id in build_ids:
            test_data = self.client.query(SELECT_TEST_DATA.format(_id))
            tests_data.append(test_data)
        tests_data = self.aggregate_api_test_results(tests_data)
        return tests_data

    @staticmethod
    def aggregate_api_test_results(tests_data):
        tests = []
        for test in tests_data:
            test_info = []
            request_names = []
            for request in list(test.get_points()):
                if request['request_name'] not in request_names:
                    request_names.append(request['request_name'])
            for request_name in request_names:
                request_info = {}
                for request in list(test.get_points()):
                    if request_name == request['request_name']:
                        if request['request_name'] in request_info.values():
                            request_info['1xx'] = int(request_info['1xx']) + request['1xx']
                            request_info['2xx'] = int(request_info['2xx']) + request['2xx']
                            request_info['3xx'] = int(request_info['3xx']) + request['3xx']
                            request_info['4xx'] = int(request_info['4xx']) + request['4xx']
                            request_info['5xx'] = int(request_info['5xx']) + request['5xx']
                            request_info['NaN'] = int(request_info['NaN']) + request['NaN']
                            request_info['ko'] = int(request_info['ko']) + request['ko']
                            request_info['ok'] = int(request_info['ok']) + request['ok']
                            request_info['total'] = int(request_info['total']) + request['total']
                            request_info['max_array'].append(int(request['max']))
                            request_info['min_array'].append(int(request['min']))
                            request_info['mean_array'].append(int(request['mean']))
                            request_info['pct50_array'].append(int(request['pct50']))
                            request_info['pct75_array'].append(int(request['pct75']))
                            request_info['pct90_array'].append(int(request['pct90']))
                            request_info['pct95_array'].append(int(request['pct95']))
                            request_info['pct99_array'].append(int(request['pct99']))
                            request_info['throughput_array'].append(float(request['throughput']))
                        else:
                            request_info = request
                            request_info['max_array'] = [int(request_info['max'])]
                            request_info['min_array'] = [int(request_info['min'])]
                            request_info['mean_array'] = [int(request_info['mean'])]
                            request_info['pct50_array'] = [int(request_info['pct50'])]
                            request_info['pct75_array'] = [int(request_info['pct75'])]
                            request_info['pct90_array'] = [int(request_info['pct90'])]
                            request_info['pct95_array'] = [int(request_info['pct95'])]
                            request_info['pct99_array'] = [int(request_info['pct99'])]
                            request_info['throughput_array'] = [float(request_info['throughput'])]

                request_info['max'] = int(statistics.median(request_info['max_array']))
                request_info['min'] = int(statistics.median(request_info['min_array']))
                request_info['mean'] = int(statistics.median(request_info['mean_array']))
                request_info['pct50'] = int(statistics.median(request_info['pct50_array']))
                request_info['pct75'] = int(statistics.median(request_info['pct75_array']))
                request_info['pct90'] = int(statistics.median(request_info['pct90_array']))
                request_info['pct95'] = int(statistics.median(request_info['pct95_array']))
                request_info['pct99'] = int(statistics.median(request_info['pct99_array']))
                request_info['throughput'] = round(float(statistics.median(request_info['throughput_array'])), 2)
                test_info.append(request_info)

            tests.append(test_info)
        return tests

    def get_baseline(self):
        self.client.switch_database(self.args['influx_comparison_database'])
        baseline_build_id = self.client.query(
            SELECT_BASELINE_BUILD_ID.format(self.args['test'], self.args['test_type'],
                                            str(self.args['users']), self.args['test']))
        result = list(baseline_build_id.get_points())
        if len(result) == 0:
            print("Baseline not found")
            return None
        _id = result[0]['build_id']
        baseline_data = self.client.query(SELECT_TEST_DATA.format(_id))
        baseline_data = self.aggregate_api_test_results([baseline_data])
        return baseline_data[0]

    def append_thresholds_to_test_data(self, test):
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
                red_threshold = 1000
                yellow_threshold = 150
            else:
                red_threshold = int(list(threshold.get_points())[0]['red'])
                yellow_threshold = int(list(threshold.get_points())[0]['yellow'])

            if int(request[comparison_metric]) < yellow_threshold:
                request_data[comparison_metric + '_threshold'] = 'green'
            else:
                request_data[comparison_metric + '_threshold'] = 'orange'
            if int(request[comparison_metric]) >= red_threshold:
                request_data[comparison_metric + '_threshold'] = 'red'
            request_data['yellow_threshold_value'] = yellow_threshold
            request_data['red_threshold_value'] = red_threshold
            for param in params:
                request_data[param] = request[param]
            test_summary.append(request_data)
        return test_summary

    def append_ui_thresholds_to_test_data(self, test):
        params = ['request_name', 'scenario', 'suite', 'build_id', 'start_time', 'url', 'count', 'failed', 'total_time',
                  'ttl', 'tti', 'onload', 'latency', 'transfer', 'encodedBodySize', 'decodedBodySize']
        self.client.switch_database(self.args['influx_thresholds_database'])
        test_summary = []
        for page in test:
            page_data = {}
            threshold = self.client.query(SELECT_THRESHOLDS.format(str(page['request_name']), str(page['scenario'])))
            if len(list(threshold.get_points())) == 0:
                red_treshold = 1000
                yellow_treshold = 150
            else:
                red_treshold = int(list(threshold.get_points())[0]['red'])
                yellow_treshold = int(list(threshold.get_points())[0]['yellow'])
            page_data['yellow_threshold_value'] = yellow_treshold
            page_data['red_threshold_value'] = red_treshold
            median_total_time = statistics.median(page['total_time'])
            median_latency = statistics.median(page['latency'])
            time = median_total_time - median_latency
            if time < yellow_treshold:
                page_data['time_threshold'] = 'green'
            else:
                page_data['time_threshold'] = 'orange'
            if time >= red_treshold:
                page_data['time_threshold'] = 'red'
            page_data['time'] = time
            for param in params:
                page_data[param] = page[param]
            test_summary.append(page_data)
        return test_summary

    def get_ui_last_builds(self):
        self.client.switch_database(self.args['influx_ui_tests_database'])
        tests_data = []
        build_ids = []
        last_builds = self.client.query(
            SELECT_LAST_UI_BUILD_ID.format(self.args['test'], str(self.args['test_type']),
                                           str(self.args['test_limit'])))
        for test in list(last_builds.get_points()):
            build_ids.append(test['distinct'])
        for _id in build_ids:
            test_data = self.client.query(SELECT_UI_TEST_DATA.format(_id))
            tests_data.append(test_data)
        return tests_data

    @staticmethod
    def aggregate_ui_test_results(tests):
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
