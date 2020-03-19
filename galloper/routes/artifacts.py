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


@bp.route("/artifacts/<string:bucket>/upload", methods=["POST"])
@project_required
def upload(project: Project, bucket: str):
    if "file" in request.files:
        f = request.files["file"]
        MinioClient(project=project).upload_file(bucket, f.read(), f.filename)
    return redirect(url_for("artifacts.index", q=bucket), code=302)


@bp.route("/artifacts/<string:bucket>/<string:fname>/delete", methods=["GET"])
@project_required
def delete(project: Project, bucket, fname):
    MinioClient(project=project).remove_file(bucket, fname)
    return redirect(url_for("artifacts.index", q=bucket), code=302)


@bp.route("/artifacts/<string:bucket>/<string:fname>", methods=["GET"])
@project_required
def download(project: Project, bucket: str, fname: str):
    fobj = MinioClient(project=project).download_file(bucket, fname)
    return send_file(BytesIO(fobj), attachment_filename=fname)


@bp.route("/artifacts/bucket", methods=["POST"])
@project_required
def create_bucket(project: Project):
    bucket = request.form["bucket"]
    res = MinioClient(project=project).create_bucket(bucket)
    if not res:
        return redirect(url_for("artifacts.index"), code=302)
    return redirect(url_for("artifacts.index", q=bucket), code=302)


@bp.route("/artifacts/<string:bucket>/delete", methods=["GET"])
@project_required
def delete_bucket(project: Project, bucket: str):
    MinioClient(project=project).remove_bucket(bucket)
    return redirect(url_for("artifacts.index"), code=302)
