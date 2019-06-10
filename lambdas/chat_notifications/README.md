# Chat notifications. Release-1.0
Lambda function that provide chat notifications

To run the lambda function, you need to create a task in the Galloper and specify a lambda handler in it.

`lambda_function.lambda_handler` - handler for all type tests notifications

You can use curl to invoke a task, example below

```
curl -XPOST -H "Content-Type: application/json"
    -d '{"param1": "value1", "param2": "value2", ...}' <host>:5000/<webhook>
```

`<host>` - Galloper host DNS or IP

`<webhook>` - POST Hook to call your task

You can pass the necessary parameters with the -d option. List of available parameters:

Required parameters

`'test': '<test_name>'` - required for all type of notifications

`'test_suite': '<ui_suite_name>'` - required for ui chat notifications

`'test_type': '<test_type>'` - required for api chat notifications

`'influx_host': '<influx_host_DNS_or_IP>'` - required for all type of notifications

`'notification_type': '<test_type>'` - should be 'ui' or 'api'


Optional parameters

`'influx_port': 8086` - default - 8086

`'influx_thresholds_database': 'thresholds'` - default - 'thresholds'

`'influx_ui_tests_database': 'perfui'` - default - 'perfui'

`'influx_comparison_database': 'comparison'` - default - 'comparison'

`'influx_user': ''` - default - ''

`'influx_password': ''` - default - ''

`'users': '<count_of_vUsers>'` - default - 1

`'comparison_metric': 'pct95'` - only for api test notifications, default - 'pct95'

 
 Specific parameters for chats
 
 Slack:
 
 `'slack_channel': '<#channel_name>'`
 
 `'slack_token': '<slack_bot_token>'`
 
 [How to create slack bot](https://get.slack.help/hc/en-us/articles/115005265703-Create-a-bot-for-your-workspace)
 
 Telegram:
 
 `'telegram_channel_id': '<channel_id>'`
 
 `'telegram_bot_token': '<bot_token>'`
 
 [How to create telegram bot](https://core.telegram.org/bots)
 
 MS Teams:
 
 `'ms_teams_web_hook': '<channel_web_hook>'`
 
 [How to create webhook for MS Teams](https://docs.microsoft.com/en-us/microsoftteams/platform/concepts/connectors/connectors-using)
 