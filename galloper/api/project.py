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
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="get_selected", type=bool, default=False, location="args"),
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
        get_selected_ = args["get_selected"]
        offset_ = args["offset"]
        limit_ = args["limit"]
        search_ = args["search"]

        if get_selected_ or project_id:
            if get_selected_:
                project_id = SessionProject.get()
            project = Project.get_object_or_404(pk=project_id)
            return project.to_json()
        elif search_:
            projects = Project.query.filter(Project.name.ilike(f"%{search_}%")).limit(limit_).offset(offset_).all()
        else:
            projects = Project.query.limit(limit_).offset(offset_).all()

        return [
            project.to_json() for project in projects
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

    def delete(self, project_id: int):
        project = Project.get_object_or_404(pk=project_id)
        project.delete()
        selected_project_id = SessionProject.get()

        if project_id == selected_project_id:
            SessionProject.pop()

        return {"message": f"Successfully deleted"}
