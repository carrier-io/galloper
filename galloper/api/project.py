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

from typing import Optional, Union, Tuple

from flask_restful import Resource

from galloper.database.models.project import Project
from galloper.database.models import project_quota
from galloper.utils.api_utils import build_req_parser
from galloper.utils.auth import SessionProject


class ProjectAPI(Resource):
    get_rules = (
        dict(name="offset", type=int, default=None, location="args"),
        dict(name="limit", type=int, default=None, location="args"),
        dict(name="search", type=str, default="", location="args")
    )
    post_rules = (
        dict(name="name", type=str, location="json"),
        dict(name="owner", type=str, default=None, location="json"),
        dict(name="dast_enabled", type=str, default=None, location="json"),
        dict(name="sast_enabled", type=str, default=None, location="json"),
        dict(name="performance_enabled", type=str, default=None, location="json"),
        dict(name="package", type=str, default="Basic", location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: Optional[int] = None) -> Union[Tuple[dict, int], Tuple[list, int]]:
        args = self._parser_get.parse_args()
        offset_ = args["offset"]
        limit_ = args["limit"]
        search_ = args["search"]

        if project_id:
            project = Project.query.get_or_404(project_id)
            return project.to_json(exclude_fields=Project.API_EXCLUDE_FIELDS), 200
        elif search_:
            projects = Project.query.filter(Project.name.ilike(f"%{search_}%")).limit(limit_).offset(offset_).all()
        else:
            projects = Project.query.limit(limit_).offset(offset_).all()

        return [
                   project.to_json(exclude_fields=Project.API_EXCLUDE_FIELDS) for project in projects
               ], 200

    def post(self, project_id: Optional[int] = None) -> Tuple[dict, int]:
        data = self._parser_post.parse_args()
        name_ = data["name"]
        owner_ = data["owner"]
        dast_enabled_ = False if data["dast_enabled"] == "disabled" else True
        sast_enabled_ = False if data["sast_enabled"] == "disabled" else True
        performance_enabled_ = False if data["performance_enabled"] == "disabled" else True
        if project_id:
            project = Project.query.get_or_404(project_id)
            project.name = name_
            project.project_owner = owner_
            project.dast_enabled = dast_enabled_
            project.sast_enabled = sast_enabled_
            project.performance_enabled = performance_enabled_
            project.commit()
            return {"message": f"Project with id {project.id} was successfully updated"}, 200

        project = Project(
            name=name_,
            dast_enabled=dast_enabled_,
            project_owner=owner_,
            sast_enabled=sast_enabled_,
            performance_enabled=performance_enabled_,
            package=data["package"].lower()
        )
        project.insert()
        SessionProject.set(project.id)  # Looks weird, sorry :D
        if hasattr(project_quota, data["package"].lower()):
            getattr(project_quota, data["package"].lower())(project.id)
        return {"message": f"Project was successfully created"}, 200

    def put(self, project_id: Optional[int] = None) -> Tuple[dict, int]:
        data = self._parser_post.parse_args()
        if not project_id:
            return {"message": "Specify project id"}, 400
        project = Project.query.get_or_404(project_id)
        project.name = data["name"]
        project.project_owner = data["owner"]
        project.dast_enabled = False if data["dast_enabled"] == "disabled" else True
        project.sast_enabled = False if data["sast_enabled"] == "disabled" else True
        project.performance_enabled = False if data["performance_enabled"] == "disabled" else True
        project.package = data["package"]
        project.commit()
        if hasattr(project_quota, data["package"].lower()):
            getattr(project_quota, data["package"].lower())(project.id)
        return project.to_json(exclude_fields=Project.API_EXCLUDE_FIELDS)

    def delete(self, project_id: int) -> Tuple[dict, int]:
        Project.apply_full_delete_by_pk(pk=project_id)
        return {"message": f"Project with id {project_id} was successfully deleted"}, 200


class ProjectSessionAPI(Resource):
    def get(self, project_id: Optional[int] = None) -> Tuple[dict, int]:
        if not project_id:
            project_id = SessionProject.get()
        if project_id:
            project = Project.query.get_or_404(project_id)
            return project.to_json(exclude_fields=Project.API_EXCLUDE_FIELDS), 200
        return {"message": "No project selected in session"}, 404

    def post(self, project_id: int) -> Tuple[dict, int]:
        project = Project.query.get_or_404(project_id)
        SessionProject.set(project.id)
        return {"message": f"Project with id {project.id} was successfully selected"}, 200

    def delete(self, project_id: int) -> Tuple[dict, int]:
        project = Project.query.get_or_404(project_id)
        if SessionProject.get() == project.id:
            SessionProject.pop()
        return {"message": f"Project with id {project.id} was successfully unselected"}, 200
