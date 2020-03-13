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

from .api_release import ReleaseAPI, ApiReportsAPI
from .project import ProjectAPI
from .report import ReportAPI, ReportChartsAPI, ReportsCompareAPI, SecurityReportAPI, FindingsAPI, FindingsAnalysisAPI
from .thresholds import ThresholdsAPI, RequestsAPI
from galloper.utils.api_utils import add_resource_to_api


def initialize_api_routes(api: Api):
    add_resource_to_api(api, ReleaseAPI, "/releases/<int:project_id>/api")
    add_resource_to_api(api, ApiReportsAPI, "/releases/<int:project_id>/api/reports")

    add_resource_to_api(api, ThresholdsAPI, "/thresholds/api")
    add_resource_to_api(api, RequestsAPI, "/requests/<int:project_id>/api")

    add_resource_to_api(api, ReportAPI, "/reports/<int:project_id>/api")
    add_resource_to_api(api, ReportChartsAPI, "/chart/<string:source>/<string:target>/api")
    add_resource_to_api(api, ReportsCompareAPI, "/compare/<string:target>/api")

    add_resource_to_api(api, SecurityReportAPI, "/security/api", "/security/<int:project_id>/api")
    add_resource_to_api(api, FindingsAPI, "/security/finding/api")
    add_resource_to_api(api, FindingsAnalysisAPI, "/security/fpa/api")

    add_resource_to_api(api, ProjectAPI, "/project", "/project/<int:project_id>")
