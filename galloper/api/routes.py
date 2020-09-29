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

from flask_restful import Api

from galloper.utils.api_utils import add_resource_to_api
from .api_release import ReleaseAPI, ApiReportsAPI, ReleaseApiSaturation
from .artifacts import BucketsApi, ArtifactApi
from .browsers import BrowsersAPI
from .observer_result import UIResultsAPI
from .project import ProjectAPI, ProjectSessionAPI
from .project_quota import ProjectQuotaAPI
from .project_secrets import ProjectSecretsAPI, ProjectSecretAPI
from .report import ReportAPI, ReportChartsAPI, ReportsCompareAPI, BaselineAPI, TestSaturation, ReportStatusAPI,\
    ReportPostProcessingAPI
from .security_report import SecurityReportAPI, FindingsAPI, FindingsAnalysisAPI
from .planner import TestsApiPerformance, TestApiBackend, TestApi
from .ui_planner import UITestsApiPerformance, TestApiFrontend
from .security_planner import SecuritySeedDispatcher
from .security_planner import TestsApiSecurityDAST, TestApiSecurityDAST
from .security_planner import TestsApiSecuritySAST, TestApiSecuritySAST
from .visual import VisualReportAPI, VisualResultAPI
from .task import TaskActionApi, TasksApi, TaskApi, TaskUpgradeApi
from .thresholds import BackendThresholdsAPI, UIThresholdsAPI, RequestsAPI, EnvironmentsAPI, SecurityThresholdsAPI
from .statistic import StatisticAPI
from .observer_report import UIReportsAPI
from .reporters import ReportersAPI


def initialize_api_routes(api: Api):
    add_resource_to_api(api, ReleaseAPI, "/releases/<int:project_id>")
    add_resource_to_api(api, ApiReportsAPI, "/releases/<int:project_id>/reports")
    add_resource_to_api(api, ReleaseApiSaturation, "/release/<int:project_id>/saturation")

    add_resource_to_api(api, BackendThresholdsAPI, "/thresholds/backend")
    add_resource_to_api(api, UIThresholdsAPI, "/thresholds/<int:project_id>/ui")
    add_resource_to_api(api, SecurityThresholdsAPI, "/thresholds/<int:project_id>/security")
    add_resource_to_api(api, RequestsAPI, "/requests/<int:project_id>")
    add_resource_to_api(api, EnvironmentsAPI, "/environment/<int:project_id>")

    add_resource_to_api(api, ReportAPI, "/reports/<int:project_id>")
    add_resource_to_api(api, ReportStatusAPI, "/reports/<int:project_id>/<int:report_id>/status")
    add_resource_to_api(api, ReportPostProcessingAPI, "/reports/<int:project_id>/processing")
    add_resource_to_api(api, ReportChartsAPI, "/chart/<string:source>/<string:target>")
    add_resource_to_api(api, ReportsCompareAPI, "/compare/<string:target>")
    add_resource_to_api(api, TestSaturation, "/saturation")

    add_resource_to_api(api, SecurityReportAPI, "/security/<int:project_id>")
    add_resource_to_api(api, FindingsAPI, "/security/<int:project_id>/finding")
    add_resource_to_api(api, FindingsAnalysisAPI, "/security/<int:project_id>/fpa")

    add_resource_to_api(api, ProjectAPI, "/project", "/project/<int:project_id>")
    add_resource_to_api(api, ProjectSessionAPI, "/project-session", "/project-session/<int:project_id>")
    add_resource_to_api(api, ProjectQuotaAPI, "/quota", "/quota/<int:project_id>")
    add_resource_to_api(api, ProjectSecretsAPI, "/secrets/<int:project_id>")
    add_resource_to_api(api, ProjectSecretAPI, "/secrets/<int:project_id>/<string:secret>")
    add_resource_to_api(api, ReportersAPI, "/reporters/<int:project_id>")

    add_resource_to_api(api, BucketsApi, "/artifacts/<int:project_id>/<string:bucket>")
    add_resource_to_api(api, ArtifactApi, "/artifacts/<int:project_id>/<string:bucket>/<string:filename>")

    add_resource_to_api(api, TaskActionApi, "/task/<string:task_id>/<string:action>")
    add_resource_to_api(api, TaskApi, "/task/<int:project_id>/<string:task_id>")
    add_resource_to_api(api, TasksApi, "/task/<int:project_id>")
    add_resource_to_api(api, TaskUpgradeApi, "/upgrade/<int:project_id>/task")

    add_resource_to_api(api, BaselineAPI, "/baseline/<int:project_id>")
    add_resource_to_api(api, StatisticAPI, "/statistic/<int:project_id>")

    add_resource_to_api(api, UIReportsAPI, "/observer/<int:project_id>")
    add_resource_to_api(api, UIResultsAPI, "/observer/<int:project_id>/<string:report_id>")

    add_resource_to_api(api, VisualReportAPI, "/visual/<int:project_id>")
    add_resource_to_api(api, VisualResultAPI, "/visual/<int:project_id>/<int:report_id>",
                        "/visual/<int:project_id>/<int:report_id>/<string:action>")

    add_resource_to_api(api, TestsApiPerformance, "/tests/<int:project_id>/backend")
    add_resource_to_api(api, TestApi, "/tests/<int:project_id>/<string:test_uuid>")
    add_resource_to_api(api, TestApiBackend, "/tests/<int:project_id>/backend/<int:test_id>",
                        "/tests/<int:project_id>/backend/<string:test_id>")

    add_resource_to_api(api, UITestsApiPerformance, "/tests/<int:project_id>/frontend")
    add_resource_to_api(api, TestApiFrontend, "/tests/<int:project_id>/frontend/<int:test_id>",
                        "/tests/<int:project_id>/frontend/<string:test_id>")

    add_resource_to_api(api, SecuritySeedDispatcher, "/tests/<int:project_id>/security/<string:seed>")

    add_resource_to_api(api, TestsApiSecurityDAST, "/tests/<int:project_id>/dast")
    add_resource_to_api(api, TestApiSecurityDAST, "/tests/<int:project_id>/dast/<int:test_id>",
                        "/tests/<int:project_id>/dast/<string:test_id>")

    add_resource_to_api(api, BrowsersAPI, "/browsers/<int:project_id>")

    add_resource_to_api(api, TestsApiSecuritySAST, "/tests/<int:project_id>/sast")
    add_resource_to_api(api, TestApiSecuritySAST, "/tests/<int:project_id>/sast/<int:test_id>",
                        "/tests/<int:project_id>/sast/<string:test_id>")
