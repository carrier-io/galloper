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

from flask import Blueprint, request, render_template, flash, current_app, redirect, url_for
from galloper.processors.perfui import prepareReport
import tempfile
from json import loads
from os.path import join
from shutil import rmtree

bp = Blueprint('perfui', __name__)


@bp.route('/perfui', methods=["GET", "POST"])
def index():
    pass


@bp.route('/perfui/analyze/async', methods=["GET", "POST"])
def analyze_async():
    pass


@bp.route('/perfui/analyze', methods=["GET", "POST"])
def analyze_sync():
    if request.method == "POST":
        videofolder = tempfile.mkdtemp()
        video_path = join(videofolder, "Video.mp4")
        if 'video' in request.files:
            request.files['video'].save(video_path)
        else:
            return "No Video = No Report"
        report = prepareReport(video_path, loads(request.form.get('data')), videofolder, True)
        rmtree(videofolder)
        return report.get_report()
