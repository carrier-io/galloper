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

from flask import Blueprint, request, render_template, redirect, url_for, send_file

from galloper.database.models.project import Project
from galloper.processors.minio import MinioClient
from galloper.utils.auth import project_required

bp = Blueprint("artifacts", __name__)


@bp.route("/artifacts", methods=["GET", "POST"])
@project_required
def index(project: Project):
    bucket_name = request.args.get("q", None)
    minio_client = MinioClient(project=project)
    buckets_list = minio_client.list_bucket()
    if not bucket_name or bucket_name not in buckets_list:
        return redirect(url_for("artifacts.index", q=buckets_list[0]))
    return render_template("artifacts/files.html",
                           files=minio_client.list_files(bucket_name),
                           buckets=buckets_list,
                           bucket=bucket_name)
