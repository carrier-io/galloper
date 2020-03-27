import logging
from typing import Optional

import boto3
from botocore.client import Config, ClientError
from galloper.constants import MINIO_ACCESS, MINIO_ENDPOINT, MINIO_SECRET, MINIO_REGION
from galloper.database.models.project import Project


class MinioClient:
    PROJECT_SECRET_KEY: str = "minio_aws_access"

    def __init__(self, project: Project, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(self.__class__.__name__.lower())
        self.project = project
        aws_access_key_id, aws_secret_access_key = self.extract_access_data()
        self.s3_client = boto3.client(
            "s3", endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name=MINIO_REGION
        )

    def extract_access_data(self) -> tuple:
        if self.project and self.PROJECT_SECRET_KEY in (self.project.secrets_json or {}):
            aws_access_json = self.project.secrets_json[self.PROJECT_SECRET_KEY]
            aws_access_key_id = aws_access_json.get("aws_access_key_id")
            aws_secret_access_key = aws_access_json.get("aws_secret_access_key")
            return aws_access_key_id, aws_secret_access_key
        return MINIO_ACCESS, MINIO_SECRET

    def list_bucket(self) -> list:
        return self.project.get_buckets_names()

    def list_s3_bucket(self) -> list:
        return [each["Name"] for each in self.s3_client.list_buckets().get("Buckets", {})]

    def create_bucket(self, bucket: str) -> dict:
        try:
            if bucket not in self.list_bucket():
                project_bucket = self.project.create_bucket(bucket_name=bucket)
                return self.s3_client.create_bucket(
                    ACL="public-read",
                    Bucket=project_bucket.internal_bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": MINIO_REGION}
                )
        except ClientError as client_error:
            self._logger.warning(str(client_error))
        except Exception as exc:
            self._logger.error(str(exc))

        return {}

    def list_files(self, bucket: str) -> list:
        bucket = self.project.get_bucket_internal_name(bucket_name=bucket)

        if bucket:
            response = self.s3_client.list_objects_v2(Bucket=bucket)
            files = [
                {"name": each["Key"], "size": each["Size"],
                 "modified": each["LastModified"].strftime("%Y-%m-%d %H:%M:%S")}
                for each in response.get("Contents", {})
            ]
            continuation_token = response.get("NextContinuationToken")
            while continuation_token and response["Contents"]:
                response = self.s3_client.list_objects_v2(Bucket=bucket,
                                                          ContinuationToken=continuation_token)
                appendage = [
                    {"name": each["Key"],
                     "size": each["Size"],
                     "modified": each["LastModified"].strftime("%Y-%m-%d %H:%M:%S")}
                    for each in response.get("Contents", {})
                ]
                if not appendage:
                    break
                files += appendage
                continuation_token = response.get("NextContinuationToken")
            return files
        return []

    def upload_file(self, bucket: str, file_obj, file_name: str):
        bucket = self.project.get_bucket_internal_name(bucket_name=bucket)
        return self.s3_client.put_object(Key=file_name, Bucket=bucket, Body=file_obj)

    def download_file(self, bucket: str, file_name: str):
        bucket = self.project.get_bucket_internal_name(bucket_name=bucket)
        return self.s3_client.get_object(Bucket=bucket, Key=file_name)["Body"].read()

    def remove_file(self, bucket: str, file_name: str):
        bucket = self.project.get_bucket_internal_name(bucket_name=bucket)
        return self.s3_client.delete_object(Bucket=bucket, Key=file_name)

    def remove_bucket(self, bucket: str):
        for file_obj in self.list_files(bucket):
            self.remove_file(bucket, file_obj["name"])

        bucket_internal_name = self.project.get_bucket_internal_name(bucket_name=bucket)
        self.project.delete_bucket(bucket_name=bucket)
        self.s3_client.delete_bucket(Bucket=bucket_internal_name)

    def configure_bucket_lifecycle(self, bucket: str, days: int) -> None:
        bucket = self.project.get_bucket_internal_name(bucket_name=bucket)
        self.s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket,
            LifecycleConfiguration={
                "Rules": [
                    {
                        "Expiration": {
                            "Days": days,
                            "ExpiredObjectDeleteMarker": True
                        },
                        "ID": "bucket-retention-policy",
                        "Status": "Enabled"
                    }
                ]
            }
        )

    def get_bucket_lifecycle(self, bucket: str) -> dict:
        bucket = self.project.get_bucket_internal_name(bucket_name=bucket)
        return self.s3_client.get_bucket_lifecycle(Bucket=bucket)
