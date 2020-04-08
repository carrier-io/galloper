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

import json
import os

from flask_restful import Resource

from galloper.database.models.project import Project
from galloper.utils.vault import create_vault_client
from galloper.utils.api_utils import build_req_parser

class ProjectSecretsApi(Resource):
    get_rules = (
        dict(name='keys[]', type=str, action='append', location='args'),
    )

    def __init__(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=True)
        if not args['keys[]']:
            return '{}'

        project = Project.query.get_or_404(project_id)
        vault = create_vault_client(project)

        secrets = vault.get_secrets()
        return json.dumps(
            {secret_key: secrets[secret_key] for secret_key in args['keys[]']}
        )

