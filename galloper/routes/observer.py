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

import tempfile
from json import loads
from os.path import join
from shutil import rmtree
from time import sleep

from flask import Blueprint, request, render_template, current_app, redirect, url_for

from galloper.constants import check_ui_performance
from galloper.processors.minio import MinioClient
from galloper.processors.perfui import prepareReport

bp = Blueprint("observer", __name__)


@bp.route("/observer", methods=["GET"])
def index():
    message = request.args.get("message", "")
    hidden = ""
    if message:
        hidden = "show"
    return render_template("observer/test.html", message=message, hidden=hidden)


@bp.route("/observer/analyze/async", methods=["GET", "POST"])
def analyze_async():
    pass


@bp.route("/observer/analyze", methods=["POST"])
def analyze_sync():
    videofolder = tempfile.mkdtemp()
    video_path = join(videofolder, "Video.mp4")
    if "video" in request.files:
        request.files["video"].save(video_path)
    else:
        return "No Video = No Report"
    report = prepareReport(video_path, loads(request.form.get("data")), videofolder, True)
    rmtree(videofolder)
    return report.get_report()


@bp.route("/observer/test", methods=["POST"])
def run_test():
    current_app.logger.info(request.form)
    url = request.form.get("url")
    remote_driver_address = request.form.get("remote_address", "127.0.0.1:4444")
    listener_address = request.form.get("perfui_listener", "127.0.0.1:9999")
    from selenium import webdriver
    from requests import get
    from time import time
    start_time = time()
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1360,1020")
    driver = webdriver.Remote(
        command_executor=f"http://{remote_driver_address}/wd/hub",
        desired_capabilities=chrome_options.to_capabilities())
    get(f"http://{listener_address}/record/start")
    current_time = time() - start_time
    driver.get(url)
    while not driver.execute_script(
        "return document.readyState === \"complete\" && performance.timing.loadEventEnd > 0"
    ):
        sleep(0.1)
    results = driver.execute_script(check_ui_performance)
    video_results = get(f"http://{listener_address}/record/stop").content
    results["info"]["testStart"] = int(current_time)
    driver.quit()
    videofolder = tempfile.mkdtemp()
    video_path = join(videofolder, "Video.mp4")
    current_app.logger.info(videofolder)
    with open(video_path, "w+b") as f:
        f.write(video_results)
    report = prepareReport(video_path, results, videofolder, True)
    # rmtree(videofolder)
    report = report.get_report()
    report_name = f"{results['info']['title']}_{int(start_time)}.html"
    MinioClient().upload_file("reports", report, report_name)
    return redirect(
        url_for("observer.index", message=f"/artifacts/reports/{report_name}"),
        code=302
    )
