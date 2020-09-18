# pylint: disable=C0111

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

from typing import Tuple

from flask_restful import Resource  # pylint: disable=E0401

from galloper.database.models.project import Project
from galloper.utils.api_utils import build_req_parser
from galloper.dal.vault import get_project_secrets, set_project_secrets, get_project_hidden_secrets


class ProjectSecretsAPI(Resource):  # pylint: disable=C0111
    post_rules = (
        dict(name="secrets", type=dict, required=True, default=None, location="json"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int) -> Tuple[dict, int]:  # pylint: disable=R0201,C0111
        # Check project_id for validity
        project = Project.get_or_404(project_id)
        # Get secrets
        secrets_dict = get_project_secrets(project.id)
        resp = []
        for key in secrets_dict.keys():
            resp.append({"name": key, "secret": "******"})
        return resp

    def post(self, project_id: int) -> Tuple[dict, int]:  # pylint: disable=C0111
        data = self._parser_post.parse_args()
        # Check project_id for validity
        project = Project.get_or_404(project_id)
        # Set secrets
        set_project_secrets(project.id, data["secrets"])
        return {"message": f"Project secrets were saved"}, 200


class ProjectSecretAPI(Resource):  # pylint: disable=C0111
    post_rules = (
        dict(name="secret", type=str, required=True, default=None, location="json"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int, secret: str) -> Tuple[dict, int]:  # pylint: disable=R0201,C0111
        # Check project_id for validity
        project = Project.get_or_404(project_id)
        # Get secret
        secrets = get_project_secrets(project.id)
        _secret = secrets.get(secret) if secrets.get(secret) else get_project_hidden_secrets(project.id).get(secret)
        return {"secret": _secret}, 200

    def post(self, project_id: int, secret: str) -> Tuple[dict, int]:  # pylint: disable=C0111
        data = self._parser_post.parse_args()
        # Check project_id for validity
        project = Project.get_or_404(project_id)
        # Set secret
        secrets = get_project_secrets(project.id)
        secrets[secret] = data["secret"]
        set_project_secrets(project.id, secrets)
        return {"message": f"Project secret was saved"}, 200

    def delete(self, project_id: int, secret: str) -> Tuple[dict, int]:  # pylint: disable=C0111
        project = Project.get_or_404(project_id)
        secrets = get_project_secrets(project.id)
        if secret in secrets:
            del secrets[secret]
        set_project_secrets(project.id, secrets)
        return {"message": "deleted"}, 200
