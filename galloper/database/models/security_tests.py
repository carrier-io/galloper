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
import string
from os import path
from uuid import uuid4
from json import dumps

from sqlalchemy import Column, Integer, String, Text, JSON, ARRAY

from galloper.database.db_manager import Base
from galloper.database.abstract_base import AbstractBaseMixin
from galloper.dal.vault import unsecret


class SecurityTestsDAST(AbstractBaseMixin, Base):
    """ Security Tests: DAST """
    __tablename__ = "security_tests_dast"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    dast_target_url = Column(Text)

    def insert(self):
        if not self.test_uid:
            self.test_uid = str(uuid4())
        super().insert()

    def configure_execution_json(self, output="cc", execution=False):
        """ Create configuration for execution """
        #
        if output == "docker":
            return f'docker run --rm -i -t ' \
                   f'-e project_id={self.project_id} ' \
                   f'-e galloper_url={unsecret("{{secret.galloper_url}}", project_id=self.project_id)} ' \
                   f"-e token=\"{unsecret('{{secret.auth_token}}', project_id=self.project_id)}\" " \
                   f'getcarrier/dast:latest run ' \
                   f'-b galloper:dast_{self.test_uid} ' \
                   f'-s dast'
        #
        if output == "dusty":
            return {
                "config_version": 2,
                "suites": {
                    "dast": {
                        "settings": {
                            "project_name": f"{self.project_id}",
                            "project_description": self.name,
                            "environment_name": "target",
                            "testing_type": "DAST",
                            "scan_type": "full",
                            "build_id": self.test_uid,
                            "dast": {
                                "max_concurrent_scanners": 1
                            }
                        },
                        "scanners": {
                            "dast": {
                                "zap": {
                                    "scan_types": "all",
                                    "target": self.dast_target_url,
                                }
                            }
                        },
                        "processing": {
                            "min_severity_filter": {
                                "severity": "Info"
                            },
                        },
                        "reporters": {
                            "galloper": {
                                "url": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
                                "project_id": f"{self.project_id}",
                                "token": unsecret('{{secret.auth_token}}', project_id=self.project_id),
                            }
                        }
                    }
                }
            }
        #
        return ""

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        test_param = super().to_json()
        for key in exclude_fields:
            if key in test_param.keys():
                del test_param[key]
        return test_param
