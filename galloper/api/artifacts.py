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

from io import BytesIO
from flask import request, send_file
from flask_restful import Resource
from galloper.database.models.project import Project
from galloper.processors.minio import MinioClient
from galloper.utils.api_utils import build_req_parser


class BucketsApi(Resource):
    def get(self, project_id: int, bucket: str):
        project = Project.get_object_or_404(pk=project_id)
        return MinioClient(project=project).list_files(bucket)

    def post(self, project_id: int, bucket: str):
        project = Project.get_object_or_404(pk=project_id)
        if "file" in request.files:
            f = request.files["file"]
            MinioClient(project=project).upload_file(bucket, f.read(), f.filename)
        return {"message": "Done", "code": 200}

    def delete(self, project_id: int, bucket: str):
        project = Project.get_object_or_404(pk=project_id)
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
        project = Project.get_object_or_404(pk=project_id)
        fobj = MinioClient(project=project).download_file(bucket, filename)
        return send_file(BytesIO(fobj), attachment_filename=filename)


    def delete(self, project_id: int, bucket: str, filename: str):
        args = self._parser_delete.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        for filename in args["fname[]"]:
            MinioClient(project=project).remove_file(bucket, filename)
        return {"message": "Deleted", "code": 200}
