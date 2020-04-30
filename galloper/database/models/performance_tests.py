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
    java_opts = Column(Text)
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
            self.params["influx.port"] = 8086
        if "influx.host" not in self.params.keys():
            self.params["influx.host"] = APP_IP
        if "galloper_url" not in self.env_vars.keys():
            self.params["galloper_url"] = APP_HOST
        if "influx.db" not in self.params.keys():
            self.params["influx.db"] = self.container_mapping[self.runner]['influx_db']
        if "test_name" not in self.params.keys():
            self.params["test_name"] = self.name  # TODO: add sanitization
        if "test.type" not in self.params.keys():
            self.params["test.type"] = 'default'
        if "comparison_db" not in self.params.keys():
            self.params["comparison_db"] = 'comparison'
        if "loki_host" not in self.env_vars.keys():
            self.params["loki_host"] = EXTERNAL_LOKI_HOST
        if "loki_port" not in self.env_vars.keys():
            self.params["loki_port"] = 3100
        self.job_type = self.container_mapping[self.runner]['job_type']
        self.runner = self.container_mapping[self.runner]['container']  # here because influx_db

        super().insert()

    def configure_execution_json(self, output='cc', test_type=None, params=None, env_vars=None, reporting=None,
                                 customization=None, java_opts=None, parallel=None):
        if not java_opts:
            java_opts = self.java_opts
        pairs = {
            "customization": [customization, self.customization],
            "params": [params, self.params],
            "env_vars": [env_vars, self.env_vars],
            "reporting": [reporting, self.reporting]
        }
        for pair in pairs.keys():
            if not pairs[pair][0]:
                pairs[pair][0] = pairs[pair][1]
            else:
                for each in set(self.pairs[pair][1].keys()) - set(pairs[pair][0].keys()):
                    pairs[pair][0][each] = self.pairs[pair][1][each]
        cmd = ''
        if self.job_type == 'perfmeter':
            entrypoint = self.entrypoint if path.exists(self.entrypoint) else path.join('/mnt/jmeter', self.entrypoint)
            cmd = f"-n -t {entrypoint}"
            for key, value in self.params.items():
                if test_type and key == "test.type":
                    cmd += f" -Jtest.type={test_type}"
                else:
                    cmd += f" -J{key}={value}"
        execution_json = {
            "container": self.runner,
            "execution_params": {
                "cmd": cmd
            },
            "bucket": self.bucket,
            "artifact": self.file,
            "job_type": self.job_type,
            "concurrency": self.parallel if not parallel else parallel
        }
        if self.env_vars:
            for key, value in self.env_vars.items():
                execution_json["execution_params"][key] = value
        if java_opts:
            execution_json["execution_params"]['JVM_ARGS'] = java_opts
        if self.customization:
            for key, value in self.customization.items():
                if "additional_files" not in execution_json["execution_params"]:
                    execution_json["execution_params"]["additional_files"] = dict()
                execution_json["execution_params"]["additional_files"][key] = value
        if self.job_type == "perfgun":
            execution_json["execution_params"]['test'] = self.entrypoint
            execution_json["execution_params"]["GATLING_TEST_PARAMS"] = ""
            for key, value in self.params.items():
                execution_json["execution_params"]["GATLING_TEST_PARAMS"] += f"-D{key}={value} "
        execution_json["execution_params"] = dumps(execution_json["execution_params"])
        if output == 'cc':
            return execution_json
        else:
            return f"docker run -e project_id={self.project_id} -e REDIS_HOST={APP_IP} " \
                   f"-e loki_host={EXTERNAL_LOKI_HOST} -e GALLOPER_WEB_HOOK={APP_HOST}/task/%s " \
                   f"-e galloper_url={APP_HOST} getcarrier/control_tower:latest " \
                   f"--container {self.runner} --execution_params '{execution_json['execution_params']}' " \
                   f"--job_type {self.job_type} --job_name {self.name} --concurrency {execution_json['concurrency']} " \
                   f"--bucket {self.bucket} --artifact {self.file}"

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        test_param = super().to_json()
        for key in exclude_fields:
            if self.params.get(key):
                del test_param['params'][key]
            else:
                del test_param[key]
        return test_param



