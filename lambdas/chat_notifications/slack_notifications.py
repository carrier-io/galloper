from slackclient import SlackClient
import json


class SlackNotifications:
    def __init__(self, arguments):
        self.args = arguments

    def api_notifications(self, summary, last_test_data, previous_test):
        text = "*Test Execution Summary*"
        message = self.create_slack_api_attachment(summary, last_test_data, previous_test,
                                                   self.args['comparison_metric'])
        sc = SlackClient(self.args['slack_token'])
        sc.api_call("chat.postMessage", channel=self.args['slack_channel'], text=text,
                    attachments=message)

    def create_slack_api_attachment(self, summary, test, previous_test, comparison_metric):
        fields = []
        summary_fields = self.get_summary_fields(summary)
        thresholds_fields = self.get_threshold_fields(test, comparison_metric)
        comparison_fields = self.get_comparison_fields(test, previous_test, comparison_metric)
        fields.extend(summary_fields)
        fields.extend(thresholds_fields)
        fields.extend(comparison_fields)

        attachment_dict = dict(
            fallback="Test info",
            fields=fields
        )
        attachment = "[" + json.dumps(attachment_dict) + "]"
        return attachment

    @staticmethod
    def get_summary_fields(summary):
        summary_field = '*Test:* {}\n' \
                        '*vUsers count:* {}\n' \
                        '*Start time:* {}\n' \
                        '*End time:* {}\n' \
                        '*Duration:* {} sec\n'
        summary_field = summary_field.format(summary['simulation'], summary['users'], summary['start'], summary['end'],
                                             summary['duration'])
        status_field = "*STATUS* {}\n"
        status = "`FAILED`" if (summary['status'] is 'FAILED') else "SUCCESS"
        status_field = status_field.format(status)
        if summary['status'] is 'FAILED':
            status_field += "*Failed reasons:*" + "\n"
            status_field += "\n".join(summary['failed_reason'])
        fields = [{"title": "", "value": summary_field, "short": True},
                  {"title": "", "value": status_field, "short": True}]
        return fields

    @staticmethod
    def get_threshold_fields(test, comparison_metric):
        yellow_thresholds = ''
        red_thresholds = ''
        fields = [{"title": "", "value": "", "short": "false"}, {"title": "", "value": "", "short": "false"}]
        threshold_message = "*{}* - {} ms\n(expected up to {} ms)\n"
        for req in test:
            if req[comparison_metric + "_threshold"] is 'yellow':
                yellow_thresholds += threshold_message.format(req['request_name'], str(req[comparison_metric]),
                                                              str(req['yellow_threshold_value']))

            if req[comparison_metric + "_threshold"] is 'red':
                red_thresholds += threshold_message.format(req['request_name'], str(req[comparison_metric]),
                                                           str(req['red_threshold_value']))
        if yellow_thresholds != '':
            fields.append({"title": "`Request exceeded yellow threshold:`", "value": yellow_thresholds, "short": True})
        if red_thresholds != '':
            fields.append({"title": "`Request exceeded red threshold:`", "value": red_thresholds, "short": True})

        return fields

    @staticmethod
    def get_comparison_fields(test, previous_test, comparison_metric):
        if not previous_test:
            return []
        fields = [{"title": "", "value": "", "short": "true"}, {"title": "", "value": "", "short": "true"}]
        if str(previous_test[0]['build_id']).startswith('audit_'):
            title = "*Comparison with baseline*"
            slower = "`Slower than baseline`\n"
            faster = "\n`Faster than baseline`\n"
        else:
            title = "*Comparison with previous test*"
            slower = "`Slower than previous test`\n"
            faster = "\n`Faster than previous test`\n"
        comparison_info = "\n"
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
        fields.append({"title": title, "value": comparison_info, "short": False})
        return fields

