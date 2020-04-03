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
from galloper.database.models.project_quota import ProjectQuota
from galloper.utils.api_utils import build_req_parser


class ProjectQuotaAPI(Resource):
    get_rules = (
        dict(name="offset", type=int, default=None, location="args"),
        dict(name="limit", type=int, default=None, location="args")
    )
    post_rules = (
        dict(name="performance_test_runs", type=int, required=False, default=None, location="json"),
        dict(name="code_repositories", type=int, required=False, default=None, location="json"),
        dict(name="dast_scans", type=int, required=False, default=None, location="json"),
        dict(name="public_pool_workers", required=False, default=None, type=int, location="json"),
        dict(name="storage_space", type=int, required=False, default=None, location="json"),
        dict(name="data_retention_limit", required=False, default=None, type=int, location="json"),
        dict(name="tasks_limit", type=int, required=False, default=None, location="json")
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

        if project_id:
            project_quota = ProjectQuota.query.filter_by(project_id=project_id).first_or_404()
            return project_quota.to_json(), 200

        project_quotas = ProjectQuota.query.limit(limit_).offset(offset_).all()
        return [project.to_json() for project in project_quotas], 200

    def post(self, project_id: Optional[int] = None) -> Tuple[dict, int]:
        data = self._parser_post.parse_args()
        project = Project.query.get_or_404(project_id)
        project_quota = ProjectQuota(
            project_id=project.id, performance_test_runs=data["performance_test_runs"],
            code_repositories=data["code_repositories"], dast_scans=data["dast_scans"],
            public_pool_workers=data["public_pool_workers"], storage_space=data["storage_space"],
            data_retention_limit=data["data_retention_limit"], tasks_limit=data["tasks_limit"]
        )
        project_quota.insert()
        return {"message": f"ProjectQuota was successfully created"}, 201

    def delete(self, project_id: int) -> Tuple[dict, int]:
        ProjectQuota.query.filter_by(project_id=project_id).delete()
        ProjectQuota.commit()
        return {"message": f"ProjectQuota with project_id {project_id} was successfully deleted"}, 200
