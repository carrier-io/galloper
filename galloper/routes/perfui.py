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

from flask import Blueprint, request
from galloper.processors.perfui import prepareReport
from galloper.constants import check_ui_performance
import tempfile
from time import sleep
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


@bp.route('/perfui/test', methods=["POST"])
def run_test():
    url = request.form.get('url')
    remote_driver_address = request.form.get("remote_address", "127.0.0.1:4444")
    listener_address = request.form.get("perfui_listener", "127.0.0.1:9999")
    from selenium import webdriver
    from requests import get
    from time import time
    start_time = time()
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--window-size=1360,1020')
    driver = webdriver.Remote(
        command_executor=f'http://{remote_driver_address}/wd/hub',
        desired_capabilities=chrome_options.to_capabilities())
    get(f'http://{listener_address}/record/start')
    current_time = time() - start_time
    driver.get(url)
    while not driver.execute_script('return document.readyState === "complete" && performance.timing.loadEventEnd > 0'):
        sleep(0.1)
    results = driver.execute_script(check_ui_performance)
    video_results = get(f'http://{listener_address}/record/stop').content
    results['info']['testStart'] = int(current_time)
    driver.quit()
    videofolder = tempfile.mkdtemp()
    video_path = join(videofolder, "Video.mp4")
    with open(video_path, 'w+b') as f:
        f.write(video_results)
    report = prepareReport(video_path, results, videofolder, True)
    #rmtree(videofolder)
    return report.get_report()


