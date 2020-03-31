#     Copyright 2020 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from datetime import datetime
from io import BytesIO

from dateutil.relativedelta import relativedelta
from flask import request, send_file
from flask_restful import Resource

from galloper.database.models.project import Project
from galloper.processors.minio import MinioClient
from galloper.utils.api_utils import build_req_parser


class BucketsApi(Resource):
    post_rules = (
        dict(name="expiration_measure", type=str, location="json",
             choices=("days", "weeks", "months", "years"),
             help="Bad choice: {error_msg}"),
        dict(name="expiration_value", type=int, location="json", required=False),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int, bucket: str):
        project = Project.query.get_or_404(project_id)
        return MinioClient(project=project).list_files(bucket)

    def post(self, project_id: int, bucket: str):
        args = self._parser_post.parse_args()
        expiration_measure = args["expiration_measure"]
        expiration_value = args["expiration_value"]

        project = Project.query.get_or_404(project_id)
        minio_client = MinioClient(project=project)
        created = minio_client.create_bucket(bucket)
        if created and expiration_value and expiration_measure:
            today_date = datetime.today().date()
            expiration_date = today_date + relativedelta(**{expiration_measure: expiration_value})
            time_delta = expiration_date - today_date
            minio_client.configure_bucket_lifecycle(bucket=bucket, days=time_delta.days)
        return {"message": "Created", "code": 200}

    def delete(self, project_id: int, bucket: str):
        project = Project.query.get_or_404(project_id)
        MinioClient(project=project).remove_bucket(bucket)
        return {"message": "Deleted", "code": 200}


class ArtifactApi(Resource):
    delete_rules = (
        dict(name="fname[]", type=str, action="append", location="args"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def get(self, project_id: int, bucket: str, filename: str):
        project = Project.query.get_or_404(project_id)
        fobj = MinioClient(project=project).download_file(bucket, filename)
        return send_file(BytesIO(fobj), attachment_filename=filename)

    def post(self, project_id: int, bucket: str, filename: str):
        project = Project.query.get_or_404(project_id)
        if "file" in request.files:
            f = request.files["file"]
            MinioClient(project=project).upload_file(bucket, f.read(), f.filename)
        return {"message": "Done", "code": 200}

    def delete(self, project_id: int, bucket: str, filename: str):
        args = self._parser_delete.parse_args(strict=False)
        project = Project.query.get_or_404(project_id)
        for filename in args.get("fname[]", ()) or ():
            MinioClient(project=project).remove_file(bucket, filename)
        return {"message": "Deleted", "code": 200}
