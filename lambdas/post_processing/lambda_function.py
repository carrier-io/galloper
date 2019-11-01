import json
from perfreporter.post_processor import PostProcessor


def lambda_handler(event, context):
    try:
        args, aggregated_errors, config_file = parse_event(event)
        post_processor = PostProcessor(args, aggregated_errors, None, config_file)
        post_processor.post_processing()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
    return {
        'statusCode': 200,
        'body': json.dumps('Done')
    }


def parse_event(_event):

    # Galloper or AWS Lambda service
    event = _event if not _event.get('body') else json.loads(_event['body'])

    args = json.loads(event.get('arguments'))
    aggregated_errors = json.loads(event.get('aggregated_errors'))
    config_file = json.loads(event.get('config_file'))

    return args, aggregated_errors, config_file
