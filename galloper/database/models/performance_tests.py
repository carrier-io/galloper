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
from os import path
from uuid import uuid4
from json import dumps

from sqlalchemy import Column, Integer, String, Text, JSON, ARRAY

from galloper.database.db_manager import Base
from galloper.database.abstract_base import AbstractBaseMixin
from galloper.constants import APP_IP, APP_HOST, EXTERNAL_LOKI_HOST
from galloper.dal.vault import get_project_secrets, unsecret

class PerformanceTests(AbstractBaseMixin, Base):
    __tablename__ = "performance_tests"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    parallel = Column(Integer, nullable=False)
    bucket = Column(String(128), nullable=False)
    file = Column(String(128), nullable=False)
    entrypoint = Column(String(128), nullable=False)
    runner = Column(String(128), nullable=False)
    reporting = Column(ARRAY(String), nullable=False)
    params = Column(JSON)
    env_vars = Column(JSON)
    customization = Column(JSON)
    cc_env_vars = Column(JSON)
    last_run = Column(Integer)
    job_type = Column(String(20))

    container_mapping = {
        "jmeter5": {
            "container": "getcarrier/perfmeter:latest",
            "job_type": "perfmeter",
            "influx_db": "jmeter"
        },
        "jmeter4": {
            "container": "getcarrier/perfmeter:latest",
            "job_type": "perfmeter",
            "influx_db": "jmeter"
        },
        "gatling2": {
            "container": "getcarrier/perfgun:2.3",
            "job_type": "perfgun",
            "influx_db": "jmeter"
        },
        "gatling3": {
            "container": "getcarrier/perfgun:latest",
            "job_type": "perfgun",
            "influx_db": "jmeter"
        }
    }

    def set_last_run(self, ts):
        self.last_run = ts
        self.commit()

    def insert(self):
        if self.runner not in self.container_mapping.keys():
            return False
        if not self.test_uid:
            self.test_uid = str(uuid4())
        if "influx.port" not in self.params.keys():
            self.params["influx.port"] = "{{secret.influx_port}}"
        if "influx.host" not in self.params.keys():
            self.params["influx.host"] = "{{secret.influx_ip}}"
        if "galloper_url" not in self.env_vars.keys():
            self.params["galloper_url"] = "{{secret.galloper_url}}"
        if "influx.db" not in self.params.keys():
            self.params["influx.db"] = self.container_mapping[self.runner]['influx_db']
        if "test_name" not in self.params.keys():
            self.params["test_name"] = self.name  # TODO: add sanitization
        if "comparison_db" not in self.params.keys():
            self.params["comparison_db"] = 'comparison'
        if "loki_host" not in self.env_vars.keys():
            self.params["loki_host"] = "{{secret.loki_host}}"
        if "loki_port" not in self.env_vars.keys():
            self.params["loki_port"] = "{{secret.loki_port}}"
        self.job_type = self.container_mapping[self.runner]['job_type']
        test_type = "test.type" if self.job_type == "perfmeter" else "test_type"
        if test_type not in self.params.keys():
            self.params[test_type] = 'default'
        self.runner = self.container_mapping[self.runner]['container']  # here because influx_db

        super().insert()

    def configure_execution_json(self, output='cc', test_type=None, params=None, env_vars=None, reporting=None,
                                 customization=None, cc_env_vars=None, parallel=None, execution=False):
        pairs = {
            "customization": [customization, self.customization],
            "params": [params, self.params],
            "env_vars": [env_vars, self.env_vars],
            "cc_env_vars": [cc_env_vars, self.cc_env_vars],
            "reporting": [reporting, self.reporting]
        }
        for pair in pairs.keys():
            if not pairs[pair][0]:
                pairs[pair][0] = pairs[pair][1]
            else:
                for each in list(pairs[pair][0].keys()) + list(set(pairs[pair][1].keys()) - set(pairs[pair][0].keys())):
                    pairs[pair][0][each] = pairs[pair][0][each] if each in list(pairs[pair][0].keys())\
                        else pairs[pair][1][each]
        cmd = ''
        if not params:
            params = self.params
        if self.job_type == 'perfmeter':
            entrypoint = self.entrypoint if path.exists(self.entrypoint) else path.join('/mnt/jmeter', self.entrypoint)
            cmd = f"-n -t {entrypoint}"
            for key, value in params.items():
                if test_type and key == "test.type":
                    cmd += f" -Jtest.type={test_type}"
                else:
                    cmd += f" -J{key}={value}"
        execution_json = {
            "container": self.runner,
            "execution_params": {
                "cmd": cmd
            },
            "cc_env_vars": {},
            "bucket": self.bucket,
            "job_name": self.name,
            "artifact": self.file,
            "job_type": self.job_type,
            "concurrency": self.parallel if not parallel else parallel
        }
        if self.reporting:
            if "junit" in self.reporting:
                execution_json["junit"] = "True"
            if "quality" in self.reporting:
                execution_json["quality_gate"] = "True"
            if "perfreports" in self.reporting:
                execution_json["save_reports"] = "True"
        if self.env_vars:
            for key, value in self.env_vars.items():
                execution_json["execution_params"][key] = value
        if self.cc_env_vars:
            for key, value in self.cc_env_vars.items():
                execution_json["cc_env_vars"][key] = value
        if self.customization:
            for key, value in self.customization.items():
                if "additional_files" not in execution_json["execution_params"]:
                    execution_json["execution_params"]["additional_files"] = dict()
                execution_json["execution_params"]["additional_files"][key] = value
        if self.job_type == "perfgun":
            execution_json["execution_params"]['test'] = self.entrypoint
            execution_json["execution_params"]["GATLING_TEST_PARAMS"] = ""
            for key, value in params.items():
                execution_json["execution_params"]["GATLING_TEST_PARAMS"] += f"-D{key}={value} "
        execution_json["execution_params"] = dumps(execution_json["execution_params"])
        if execution:
            execution_json = unsecret(execution_json, project_id=self.project_id)
        if output == 'cc':
            return execution_json
        else:
            return "docker run -e project_id=%s -e REDIS_HOST={{secret.redis_host}} " \
                   "-e loki_host={{secret.loki_host}} -e GALLOPER_WEB_HOOK={{secret.post_processor}} " \
                   "-e galloper_url={{secret.galloper_url}} getcarrier/control_tower:latest " \
                   "--container %s --execution_params '%s' " \
                   "--job_type %s --job_name %s --concurrency %s --bucket %s --artifact %s" \
                   "" % (self.project_id, self.runner, execution_json['execution_params'], self.job_type,
                         self.name, execution_json['concurrency'], self.bucket, self.file)

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        test_param = super().to_json()
        for key in exclude_fields:
            if self.params.get(key):
                del test_param['params'][key]
            elif key in test_param.keys():
                del test_param[key]
        return test_param



