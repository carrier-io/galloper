import boto3
from botocore.client import Config
from galloper.constants import MINIO_ACCESS, MINIO_ENDPOINT, MINIO_SECRET, MINIO_REGION

s3_client = None


def get_client():
    global s3_client
    if not s3_client:
        s3_client = boto3.client('s3', endpoint_url=MINIO_ENDPOINT,
                                 aws_access_key_id=MINIO_ACCESS,
                                 aws_secret_access_key=MINIO_SECRET,
                                 config=Config(signature_version='s3v4'),
                                 region_name=MINIO_REGION)
    return s3_client


def list_bucket():
    return [each['Name'] for each in get_client().list_buckets().get('Buckets', {})]


def create_bucket(name):
    try:
        if name not in list_bucket():
            return get_client().create_bucket(
                ACL='public-read', Bucket=name, CreateBucketConfiguration={'LocationConstraint': MINIO_REGION}
            )
    except:
        return {}


def list_files(bucket_name):
    response = get_client().list_objects_v2(Bucket=bucket_name)
    files = [
        {'name': each['Key'], 'size': each['Size'], 'modified': each['LastModified']}
        for each in response.get('Contents', {})
    ]
    continuation_token = response.get('NextContinuationToken')
    while continuation_token and response['Contents']:
        response = get_client().list_objects_v2(Bucket=bucket_name,
                                                ContinuationToken=continuation_token)
        appendage = [
            {'name': each['Key'], 'size': each['Size'], 'modified': each['LastModified']}
            for each in response.get('Contents', {})
        ]
        if not appendage:
            break
        files += appendage
        continuation_token = response.get('NextContinuationToken')
    return files


def upload_file(bucket, file_obj, file_name):
    return get_client().put_object(Key=file_name, Bucket=bucket, Body=file_obj)


def download_file(bucket, filename):
    return get_client().get_object(Bucket=bucket, Key=filename)['Body'].read()


def remove_file(bucket, filename):
    return get_client().delete_object(Bucket=bucket, Key=filename)


def remove_bucket(bucket):
    for fileobj in list_files(bucket):
        remove_file(bucket, fileobj['name'])
    get_client().delete_bucket(Bucket=bucket)
