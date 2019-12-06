#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from flask import Blueprint, request, render_template, redirect, url_for, send_file
from galloper.processors import minio
from galloper.constants import check_ui_performance
import tempfile
from time import sleep
from json import loads
from os.path import join
from shutil import rmtree
from io import BytesIO

bp = Blueprint('artifacts', __name__)


@bp.route('/artifacts', methods=["GET", "POST"])
def index():
    bucket_name = request.args.get("q", None)
    buckets_list = minio.list_bucket()
    if not bucket_name or bucket_name not in buckets_list:
        return redirect(url_for('artifacts.index', q=buckets_list[0]))
    return render_template('artifacts/files.html', 
                           files=minio.list_files(bucket_name), 
                           buckets=buckets_list,
                           bucket=bucket_name)

@bp.route('/artifacts/<bucket>/upload', methods=["POST"])
def upload(bucket):
    if 'file' in request.files:
        f = request.files['file']
        minio.upload_file(bucket, f.read(), f.filename)
    return redirect(url_for('artifacts.index', q=bucket), code=302)

@bp.route('/artifacts/<bucket>/<fname>/delete', methods=["GET"])
def delete(bucket, fname):
    minio.remove_file(bucket, fname)
    return redirect(url_for('artifacts.index', q=bucket), code=302)
    

@bp.route('/artifacts/<bucket>/<fname>', methods=["GET"])
def download(bucket, fname):
    fobj = minio.download_file(bucket, fname)
    return send_file(BytesIO(fobj), attachment_filename=fname)

@bp.route('/artifacts/bucket', methods=["POST"])
def create_bucket():
    bucket = request.form['bucket']
    res = minio.create_bucket(bucket)
    if not res:
        return redirect(url_for('artifacts.index'), code=302)
    return redirect(url_for('artifacts.index', q=bucket), code=302)

@bp.route('/artifacts/<bucket>/delete', methods=["GET"])
def delete_bucket(bucket):
    minio.remove_bucket(bucket)
    return redirect(url_for('artifacts.index'), code=302)