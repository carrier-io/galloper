from influxdb import InfluxDBClient
import datetime
import statistics


SELECT_LAST_BUILD_ID = "select distinct(id) from (select build_id as id, count from uiperf where scenario=\'{}\' and" \
                       " suite=\'{}\' group by start_time order by time DESC limit 1) GROUP BY time(1s)" \
                       " order by DESC limit 1"

SELECT_TEST_DATA = "select build_id, scenario, suite, domain, start_time, page, status, url, latency, tti, ttl," \
                   " onload, total_time, transfer from uiperf where build_id=\'{}\'"

SELECT_THRESHOLDS = "select last(red) as red, last(yellow) as yellow from threshold where request_name=\'{}\' " \
                    "and simulation=\'{}\'"


class UIDataManager:

    def __init__(self, arguments):
        self.args = arguments
        self.client = InfluxDBClient(arguments['influx_host'], arguments['influx_port'],
                                     username=arguments['influx_user'], password=arguments['influx_password'])

    def prepare_ui_test_data(self):
        test_data = self.get_ui_last_build()
        if not test_data:
            raise Exception("No data found for given parameters")
        test_data = self.aggregate_results(test_data)
        test_data = self.append_ui_thresholds_to_test_data(test_data)
        summary = self.create_ui_test_summary(test_data)
        return summary, test_data

    def get_ui_last_build(self):
        self.client.switch_database(self.args['influx_ui_tests_database'])
        build_id = self.client.query(SELECT_LAST_BUILD_ID.format(self.args['test'], str(self.args['test_type'])))
        _id = list(build_id.get_points())[0]['distinct']
        test_data = self.client.query(SELECT_TEST_DATA.format(_id))
        return list(test_data.get_points())

    def append_ui_thresholds_to_test_data(self, test):
        params = ['page_name', 'scenario', 'suite', 'start_time', 'count', 'failed', 'total_time',
                  'ttl', 'tti', 'latency', 'transfer']
        self.client.switch_database(self.args['influx_thresholds_database'])
        test_summary = []
        for page in test:
            page_data = {}
            thresholds = self.client.query(SELECT_THRESHOLDS.format(str(page['page_name']), str(page['scenario'])))
            if len(list(thresholds.get_points())) == 0:
                red_threshold = 1000
                yellow_threshold = 150
            else:
                red_threshold = int(list(thresholds.get_points())[0]['red'])
                yellow_threshold = int(list(thresholds.get_points())[0]['yellow'])
            page_data['yellow_threshold_value'] = yellow_threshold
            page_data['red_threshold_value'] = red_threshold
            total_time = int(page['total_time']) - int(page['latency'])
            if total_time >= red_threshold:
                page_data['threshold'] = 'red'
            elif total_time >= yellow_threshold:
                page_data['threshold'] = 'yellow'
            else:
                page_data['threshold'] = 'green'
            page_data['time'] = total_time
            for param in params:
                page_data[param] = page[param]
            test_summary.append(page_data)
        self.client.close()
        return test_summary

    @staticmethod
    def aggregate_results(test):
        test_data = {}
        for page in test:
            if page['page'] not in test_data:
                test_data[page['page']] = {
                    'scenario': page['scenario'],
                    'suite': page['suite'],
                    'start_time': page['start_time'],
                    'page_name': page['page'],
                    'count': 1,
                    'failed': 0,
                    'total_time': [page['total_time']],
                    'ttl': [page['ttl']],
                    'tti': [page['tti']],
                    'latency': [page['latency']],
                    'transfer': [page['transfer']]
                }
                if page['status'] == 'ko':
                    test_data[page['page']]['failed'] = int(test_data[page['page']]['failed']) + 1
            else:
                test_data[page['page']]['total_time'].append(page['total_time'])
                test_data[page['page']]['ttl'].append(page['ttl'])
                test_data[page['page']]['tti'].append(page['tti'])
                test_data[page['page']]['latency'].append(page['latency'])
                test_data[page['page']]['transfer'].append(page['transfer'])
                test_data[page['page']]['count'] = int(test_data[page['page']]['count']) + 1
                if page['status'] == 'ko':
                    test_data[page['page']]['failed'] = int(test_data[page['page']]['failed']) + 1
        for page in test_data.values():
            page['total_time'] = statistics.median(page['total_time'])
            page['ttl'] = statistics.median(page['ttl'])
            page['tti'] = statistics.median(page['tti'])
            page['latency'] = statistics.median(page['latency'])
            page['transfer'] = statistics.median(page['transfer'])
        return list(test_data.values())

    @staticmethod
    def create_ui_test_summary(test):
        summary = dict()
        summary['start'] = datetime.datetime.utcfromtimestamp(int(test[0]['start_time']) / 1000) \
            .strftime('%Y-%m-%d %H:%M:%S')
        summary['test'] = test[0]['scenario']
        summary['test_suite'] = test[0]['suite']
        count, errors = 0, 0
        for page in test:
            count += int(page['count'])
            errors += int(page['failed'])
        error_rate = round(errors * 100 / count, 2)
        failed_reasons = []
        if error_rate > 10:
            summary['status'] = 'FAILED'
            failed_reasons.append('error rate - ' + str(error_rate) + ' %')
        else:
            summary['status'] = 'SUCCESS'
        page_count = 0
        missed_thresholds = 0
        for page in test:
            page_count += 1
            if page['threshold'] != 'green':
                missed_thresholds += 1
        missed_thresholds_rate = round(missed_thresholds * 100 / page_count, 2)
        if missed_thresholds_rate > 50:
            summary['status'] = 'FAILED'
            failed_reasons.append('missed thresholds - ' + str(missed_thresholds_rate) + ' %')
        summary['failed_reason'] = failed_reasons

        return summary
