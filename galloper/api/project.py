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

from typing import Optional, Union

from flask_restful import Resource

from galloper.database.models.project import Project
from galloper.utils.api_utils import build_req_parser
from galloper.utils.auth import SessionProject


class ProjectAPI(Resource):
    SELECT_ACTION = "select"
    UNSELECT_ACTION = "unselect"

    get_rules = (
        dict(name="used_in_session", type=bool, default=False, location="args"),
    )
    post_rules = (
        dict(name="action", type=str, location="json"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: Optional[int] = None) -> Union[list, dict]:
        args = self._parser_get.parse_args()
        used_in_session = args["used_in_session"]

        if project_id:
            project = Project.get_object_or_404(pk=project_id)
            return project.to_json(used_in_session=used_in_session)

        return [
            project.to_json(used_in_session=used_in_session)
            for project in Project.query.all()
        ]

    def post(self, project_id: Optional[int] = None) -> dict:
        args = self._parser_post.parse_args()
        action = args["action"]
        if action == self.SELECT_ACTION:
            SessionProject.set(project_id)
        elif action == self.UNSELECT_ACTION:
            SessionProject.pop()

        return {
            "message": f"Successfully {action}ed" if action else "No action"
        }
