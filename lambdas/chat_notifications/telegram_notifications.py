import telegram


class TelegramNotifications(object):
    def __init__(self, arguments):
        self.args = arguments

    def api_notifications(self, summary, last_test_data, previous_test):
        text = '*Test Execution Summary*\n\n'
        text += self.create_api_test_summary(summary)
        text += self.create_api_test_thresholds_info(last_test_data, self.args['comparison_metric'])
        text += self.create_api_test_comparison_info(last_test_data, previous_test, self.args['comparison_metric'])
        bot = telegram.Bot(token=self.args['telegram_bot_token'])
        bot.send_message(chat_id=int(self.args['telegram_channel_id']), text=text, parse_mode='Markdown')

    @staticmethod
    def create_api_test_summary(summary):
        summary_info = '*Test:* {}\n' \
                       '*vUsers count:* {}\n' \
                       '*Start time:* {}\n' \
                       '*End time:* {}\n' \
                       '*Duration:* {} sec\n' \
                       '*Status:* {}'
        status = "`FAILED`\n" if (summary['status'] is 'FAILED') else "SUCCESS\n"
        summary_info = summary_info.format(summary['simulation'], summary['users'], summary['start'], summary['end'],
                                           summary['duration'], status)
        if summary['status'] is 'FAILED':
            summary_info += '*Failed reasons:*\n'
            summary_info += "\n".join(summary['failed_reason']) + "\n"
        return summary_info

    @staticmethod
    def create_api_test_thresholds_info(test, comparison_metric):
        yellow_thresholds = []
        red_thresholds = []
        threshold_message = "*{}* - {} ms. Expected up to {} ms.\n"
        for req in test:
            if req[comparison_metric + "_threshold"] is 'yellow':
                yellow_thresholds.append(threshold_message.format(req['request_name'], str(req[comparison_metric]),
                                                                  str(req['yellow_threshold_value'])))

            if req[comparison_metric + "_threshold"] is 'red':
                red_thresholds.append(threshold_message.format(req['request_name'], str(req[comparison_metric]),
                                                               str(req['red_threshold_value'])))
        thresholds_info = ''
        if yellow_thresholds:
            thresholds_info += "\n`Request exceeded yellow threshold:`\n"
            thresholds_info += "\n".join(yellow_thresholds)
        if red_thresholds:
            thresholds_info += "\n`Request exceeded red threshold:`\n"
            thresholds_info += "\n".join(red_thresholds)
        return thresholds_info

    @staticmethod
    def create_api_test_comparison_info(test, previous_test, comparison_metric):
        if not previous_test:
            return ''
        comparison_info = '\n'
        if str(previous_test[0]['build_id']).startswith('audit_'):
            title = "*Comparison with baseline*\n"
            slower = "`Slower than baseline`\n"
            faster = "\n`Faster than baseline`\n"
        else:
            title = "*Comparison with previous test*\n"
            slower = "`Slower than previous test`\n"
            faster = "\n`Faster than previous test`\n"
        comparison_info += title + "\n"
        comparison_message = "*{}* - {} ms. Was {} ms"
        slower_requests, faster_requests = [], []
        for request in test:
            for req in previous_test:
                if request['request_name'] == req['request_name']:
                    if int(request[comparison_metric]) > int(req[comparison_metric]):
                        slower_requests.append(comparison_message.format(request['request_name'],
                                                                         "`" + str(request[comparison_metric]) + "`",
                                                                         str(req[comparison_metric])))
                    elif int(request[comparison_metric]) < int(req[comparison_metric]):
                        faster_requests.append(comparison_message.format(request['request_name'],
                                                                         str(request[comparison_metric]),
                                                                         "`" + str(req[comparison_metric]) + "`"))
        if slower_requests:
            comparison_info += slower
            comparison_info += "\n".join(slower_requests) + "\n"
        if faster_requests:
            comparison_info += faster
            comparison_info += "\n".join(faster_requests)

        return comparison_info
