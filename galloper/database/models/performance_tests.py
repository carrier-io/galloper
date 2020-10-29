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
from flask import current_app
from sqlalchemy import Column, Integer, String, Text, JSON, ARRAY

from galloper.database.db_manager import Base
from galloper.database.abstract_base import AbstractBaseMixin
from galloper.dal.vault import unsecret
from galloper.constants import JOB_CONTAINER_MAPPING


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
    emails = Column(Text)
    params = Column(JSON)
    env_vars = Column(JSON)
    customization = Column(JSON)
    cc_env_vars = Column(JSON)
    git = Column(JSON)
    last_run = Column(Integer)
    job_type = Column(String(20))


    def set_last_run(self, ts):
        self.last_run = ts
        self.commit()

    @staticmethod
    def sanitize(val):
        valid_chars = "_%s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in val if c in valid_chars)

    def insert(self):
        if self.runner not in JOB_CONTAINER_MAPPING.keys():
            return False
        self.name = self.sanitize(self.name)
        if not self.test_uid:
            self.test_uid = str(uuid4())
        if "influx.port" not in self.params.keys():
            self.params["influx.port"] = "{{secret.influx_port}}"
        if "influx.host" not in self.params.keys():
            self.params["influx.host"] = "{{secret.influx_ip}}"
        if "influx_user" not in self.params.keys():
            self.params["influx.username"] = "admin"
        if "influx_password" not in self.params.keys():
            self.params["influx.password"] = "{{secret.influx_password}}"
        if "galloper_url" not in self.env_vars.keys():
            self.params["galloper_url"] = "{{secret.galloper_url}}"
        if "influx.db" not in self.params.keys():
            self.params["influx.db"] = JOB_CONTAINER_MAPPING[self.runner]['influx_db']
        if "test_name" not in self.params.keys():
            self.params["test_name"] = self.name  # TODO: add sanitization
        if "comparison_db" not in self.params.keys():
            self.params["comparison_db"] = 'comparison'
        if "loki_host" not in self.env_vars.keys():
            self.params["loki_host"] = "{{secret.loki_host}}"
        if "loki_port" not in self.env_vars.keys():
            self.params["loki_port"] = "{{secret.loki_port}}"
        self.job_type = JOB_CONTAINER_MAPPING[self.runner]['job_type']
        test_type = "test.type" if self.job_type == "perfmeter" else "test_type"
        if test_type not in self.params.keys():
            self.params[test_type] = 'default'
        self.runner = JOB_CONTAINER_MAPPING[self.runner]['container']  # here because influx_db

        super().insert()

    def configure_execution_json(self, output='cc', test_type=None, params=None, env_vars=None, reporting=None,
                                 customization=None, cc_env_vars=None, parallel=None, execution=False, emails=None):
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
                    pairs[pair][0][each] = pairs[pair][0][each] if each in list(pairs[pair][0].keys()) \
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
            if "jira" in self.reporting:
                execution_json["jira"] = "True"
            if "email" in self.reporting:
                execution_json["email"] = "True"
            if "rp" in self.reporting:
                execution_json["report_portal"] = "True"
            if "ado" in self.reporting:
                execution_json["azure_devops"] = "True"
        if emails:
            _emails = self.emails
            for each in emails.split(","):
                if each not in _emails:
                    _emails += f",{each}"
            execution_json["email_recipients"] = _emails
        else:
            execution_json["email_recipients"] = self.emails

        if self.env_vars:
            for key, value in self.env_vars.items():
                execution_json["execution_params"][key] = value
        if "influxdb_host" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_host"] = "{{secret.influx_ip}}"
        if "influxdb_user" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_user"] = "admin"
        if "influxdb_password" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["influxdb_password"] = "{{secret.influx_password}}"
        if "loki_host" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["loki_host"] = "{{secret.loki_host}}"
        if "loki_port" not in execution_json["execution_params"].keys():
            execution_json["execution_params"]["loki_port"] = "3100"
        if self.cc_env_vars:
            for key, value in self.cc_env_vars.items():
                execution_json["cc_env_vars"][key] = value
        if "REDIS_HOST" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["REDIS_HOST"] = "{{secret.redis_host}}"
        if "REDIS_PASSWORD" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["REDIS_PASSWORD"] = "{{secret.redis_password}}"
        if "GALLOPER_WEB_HOOK" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["GALLOPER_WEB_HOOK"] = "{{secret.post_processor}}"
        if self.customization:
            for key, value in self.customization.items():
                if "additional_files" not in execution_json["execution_params"]:
                    execution_json["execution_params"]["additional_files"] = dict()
                execution_json["execution_params"]["additional_files"][key] = value
        if self.git:
            execution_json["git"] = self.git
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
            return "docker run -e project_id=%s -e galloper_url=%s -e token=%s" \
                   " getcarrier/control_tower:latest --test_id=%s" \
                   "" % (self.project_id, unsecret("{{secret.galloper_url}}", project_id=self.project_id),
                         unsecret("{{secret.auth_token}}", project_id=self.project_id), self.test_uid)

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        test_param = super().to_json()
        for key in exclude_fields:
            if self.params.get(key):
                del test_param['params'][key]
            elif key in test_param.keys():
                del test_param[key]
        return test_param


class UIPerformanceTests(AbstractBaseMixin, Base):
    __tablename__ = "ui_performance_tests"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    bucket = Column(String(128), nullable=False)
    file = Column(String(128), nullable=False)
    entrypoint = Column(String(128), nullable=False)
    runner = Column(String(128), nullable=False)
    browser = Column(String(128), nullable=False)
    reporting = Column(ARRAY(String), nullable=False)
    parallel = Column(Integer, nullable=False)
    params = Column(JSON)
    env_vars = Column(JSON)
    customization = Column(JSON)
    git = Column(JSON)
    cc_env_vars = Column(JSON)
    last_run = Column(Integer)
    job_type = Column(String(20))
    emails = Column(Text)
    loops = Column(Integer)
    aggregation = Column(String(20))

    
    def configure_execution_json(self, output='cc', browser=None, test_type=None, params=None, env_vars=None, reporting=None,
                                 customization=None, cc_env_vars=None, parallel=None, execution=False):

        reports = []
        for report in self.reporting:
            if report:
                reports.append(f"-r {report}")

        cmd = f"-sc {self.entrypoint} -l {self.loops} -b {browser} " \
              f"-a {self.aggregation} {' '.join(reports)} -tid {self.test_uid}"

        execution_json = {
            "container": self.runner,
            "execution_params": {
                "cmd": cmd,
                "REMOTE_URL": f'{unsecret("{{secret.redis_host}}", project_id=self.project_id)}:4444'
            },
            "cc_env_vars": {},
            "bucket": self.bucket,
            "job_name": self.name,
            "artifact": self.file,
            "job_type": self.job_type,
            "concurrency": 1
        }

        if "jira" in self.reporting:
            execution_json["execution_params"]["JIRA"] = unsecret("{{secret.jira}}", project_id=self.project_id)

        if "ado" in self.reporting:
            execution_json["execution_params"]["ADO"] = unsecret("{{secret.ado}}", project_id=self.project_id)

        if "quality" in self.reporting:
            execution_json["quality_gate"] = True
        if "junit" in self.reporting:
            execution_json["junit"] = True

        if self.git:
            execution_json["git"] = self.git

        if self.env_vars:
            for key, value in self.env_vars.items():
                execution_json["execution_params"][key] = value

        if self.cc_env_vars:
            for key, value in self.cc_env_vars.items():
                execution_json["cc_env_vars"][key] = value
        if "REDIS_HOST" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["REDIS_HOST"] = "{{secret.redis_host}}"
        if "REDIS_PASSWORD" not in execution_json["cc_env_vars"].keys():
            execution_json["cc_env_vars"]["REDIS_PASSWORD"] = "{{secret.redis_password}}"

        if self.customization:
            for key, value in self.customization.items():
                if "additional_files" not in execution_json["execution_params"]:
                    execution_json["execution_params"]["additional_files"] = dict()
                execution_json["execution_params"]["additional_files"][key] = value
        execution_json["execution_params"] = dumps(execution_json["execution_params"])
        if execution:
            execution_json = unsecret(execution_json, project_id=self.project_id)
        if output == 'cc':
            current_app.logger.error(execution_json)
            return execution_json

        return f'docker run -t --rm -e project_id={self.project_id} ' \
               f'-e galloper_url={unsecret("{{secret.galloper_url}}", project_id=self.project_id)} ' \
               f"-e token=\"{unsecret('{{secret.auth_token}}', project_id=self.project_id)}\" " \
               f'getcarrier/control_tower:latest ' \
               f'--test_id {self.test_uid}'
