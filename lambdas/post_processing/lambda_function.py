import json
from perfreporter.post_processor import PostProcessor


def lambda_handler(event, context):
    try:
        args, comparison_data, aggregated_errors, errors, config_file = parse_event(event)
        post_processor = PostProcessor(args, aggregated_errors, errors, comparison_data, config_file)
        post_processor.distributed_mode_post_processing()

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
    test_results = json.loads(event.get('test_results'))
    aggregated_errors = json.loads(event.get('aggregated_errors'))
    errors = json.loads(event.get('errors'))
    config_file = json.loads(event.get('config_file'))

    return args, test_results, aggregated_errors, errors, config_file
