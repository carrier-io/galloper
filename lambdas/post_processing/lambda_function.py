import json
from perfreporter.post_processor import PostProcessor


def lambda_handler(event, context):
    try:
        galloper_url, bucket, prefix, config_file = parse_event(event)
        post_processor = PostProcessor(config_file)
        post_processor.distributed_mode_post_processing(galloper_url, bucket, prefix)

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

    galloper_url = event.get('galloper_url')
    bucket = event.get('bucket')
    prefix = event.get('prefix')
    config_file = json.loads(event.get('config_file'))

    return galloper_url, bucket, prefix, config_file
