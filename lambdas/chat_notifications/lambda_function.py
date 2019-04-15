from chat_notification import ChatNotification
import json


def lambda_handler(event, context):
    try:
        args = parse_args(event)

        # Check required params
        if not all([args['influx_host'], args['chat'], args['test'], args['test_type'], args['notification_type']]):
            raise Exception('Some required parameters not passed')

        # Send notification
        if args['notification_type'] == 'api':
            ChatNotification(args).api_notifications()
        elif args['notification_type'] == 'ui':
            ChatNotification(args).ui_notifications()
        else:
            raise Exception('Incorrect value for notification_type: {}. Must be api or ui'
                            .format(args['notification_type']))
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
    return {
        'statusCode': 200,
        'body': json.dumps('Notification has been sent')
    }


def parse_args(_event):
    args = {}

    # Galloper or AWS Lambda service
    event = _event if not _event.get('body') else json.loads(_event['body'])

    # Optional params
    args['influx_port'] = event.get("influx_port", 8086)
    args['influx_thresholds_database'] = event.get("influx_thresholds_database", "thresholds")
    args['influx_ui_tests_database'] = event.get("influx_ui_tests_database", "perfui")
    args['influx_comparison_database'] = event.get("influx_comparison_database", "comparison")
    args['influx_user'] = event.get("influx_user", "")
    args['influx_password'] = event.get("influx_password", "")
    args['comparison_metric'] = event.get("comparison_metric", "pct95")
    args['users'] = event.get('users', 1)

    # Required params
    args['influx_host'] = event.get('influx_host')
    args['test'] = event.get('test')
    args['notification_type'] = event.get('notification_type')
    if args['notification_type'] == 'api':
        args['test_type'] = event.get('test_type')
    if args['notification_type'] == 'ui':
        args['test_type'] = event.get('test_suite')

    # Specific params for chats
    args['slack_channel'] = event.get('slack_channel')
    args['slack_token'] = event.get('slack_token')
    args['telegram_bot_token'] = event.get('telegram_bot_token')
    args['telegram_channel_id'] = event.get('telegram_channel_id')
    args['ms_teams_web_hook'] = event.get('ms_teams_web_hook')
    if args['slack_channel'] and args['slack_token']:
        args['chat'] = 'slack'
    elif args['telegram_bot_token'] and args['telegram_channel_id']:
        args['chat'] = 'telegram'
    elif args['ms_teams_web_hook']:
        args['chat'] = 'ms_teams'
    else:
        args['chat'] = None

    return args
