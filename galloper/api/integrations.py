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

from flask_restful import Resource
from galloper.database.models.project import Project
from galloper.utils.api_utils import build_req_parser, str2bool
from galloper.utils.integration_utils import jira_integration, smtp_integration, rp_integration, ado_integration, \
    aws_integration


class IntegrationsAPI(Resource):
    post_rules = (
        dict(name="test", type=str2bool, default=False, location="json"),
        dict(name="integration", type=str, location="json"),
        dict(name="config", type=dict, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()
        self.mapper = {
            "jira": jira_integration,
            "smtp": smtp_integration,
            "rp": rp_integration,
            "ado": ado_integration,
            "aws": aws_integration
        }

    def __init_req_parsers(self):
        self.post_parser = build_req_parser(rules=self.post_rules)

    def post(self, project_id: int):
        args = self.post_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        message = self.mapper.get(args["integration"])(args, project)

        return {"message": message}
