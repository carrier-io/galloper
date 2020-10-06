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
from uuid import uuid4
from json import dumps, loads

from sqlalchemy import Column, Integer, String, Text, JSON, ARRAY

from galloper.database.db_manager import Base
from galloper.database.abstract_base import AbstractBaseMixin
from galloper.dal.vault import unsecret, get_project_hidden_secrets
from galloper.processors.minio import MinioClient
from galloper.constants import CURRENT_RELEASE

from .project import Project


class SecurityTestsDAST(AbstractBaseMixin, Base):
    """ Security Tests: DAST """
    __tablename__ = "security_tests_dast"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    dast_settings = Column(JSON)

    def insert(self):
        if not self.test_uid:
            self.test_uid = str(uuid4())
        #
        super().insert()
        #
        project = Project.query.get_or_404(self.project_id)
        minio_client = MinioClient(project=project)
        minio_client.create_bucket(bucket="dast")

    def configure_execution_json(self, output="cc", execution=False, thresholds={}):
        """ Create configuration for execution """
        #
        if output == "dusty":
            #
            global_dast_settings = dict()
            global_dast_settings["max_concurrent_scanners"] = 1
            if "toolreports" in self.dast_settings.get("reporters_checked", list()):
                global_dast_settings["save_intermediates_to"] = "/tmp/intermediates"
            #
            scanners_config = dict()
            if "zap" in self.dast_settings.get("scanners_checked", list()):
                scanners_config["zap"] = {
                    "scan_types": "all",
                    "target": self.dast_settings.get("dast_target_url"),
                }
            if "w3af" in self.dast_settings.get("scanners_checked", list()):
                scanners_config["w3af"] = {
                    "target": self.dast_settings.get("dast_target_url"),
                }
            if "nikto" in self.dast_settings.get("scanners_checked", list()):
                scanners_config["nikto"] = {
                    "target": self.dast_settings.get("dast_target_url"),
                }
            if "nmap" in self.dast_settings.get("scanners_checked", list()):
                scanners_config["nmap"] = {
                    "target": self.dast_settings.get("dast_target_url"),
                }
            if "masscan" in self.dast_settings.get("scanners_checked", list()):
                scanners_config["masscan"] = {
                    "target": self.dast_settings.get("dast_target_url"),
                }
            if "sslyze" in self.dast_settings.get("scanners_checked", list()):
                scanners_config["sslyze"] = {
                    "target": self.dast_settings.get("dast_target_url"),
                }
            if "aemhacker" in self.dast_settings.get("scanners_checked", list()):
                scanners_config["aemhacker"] = {
                    "target": self.dast_settings.get("dast_target_url"),
                }
            #
            reporters_config = dict()
            reporters_config["galloper"] = {
                "url": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
                "project_id": f"{self.project_id}",
                "token": unsecret("{{secret.auth_token}}", project_id=self.project_id),
            }
            if "toolreports" in self.dast_settings.get("reporters_checked", list()):
                reporters_config["galloper_tool_reports"] = {
                    "bucket": "dast",
                    "object": f"{self.test_uid}_tool_reports.zip",
                    "source": "/tmp/intermediates",
                }
            if "quality" in self.dast_settings.get("reporters_checked", list()):
                reporters_config["galloper_junit_report"] = {
                    "bucket": "dast",
                    "object": f"{self.test_uid}_junit_report.xml",
                }
                reporters_config["galloper_quality_gate_report"] = {
                    "bucket": "dast",
                    "object": f"{self.test_uid}_quality_gate_report.json",
                }
                reporters_config["junit"] = {
                    "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.xml",
                }
            #
            if "jira" in self.dast_settings.get("reporters_checked", list()):
                project_secrets = get_project_hidden_secrets(self.project_id)
                if "jira" in project_secrets:
                    jira_settings = loads(project_secrets["jira"])
                    reporters_config["jira"] = {
                        "url": jira_settings["jira_url"],
                        "username": jira_settings["jira_login"],
                        "password": jira_settings["jira_password"],
                        "project": jira_settings["jira_project"],
                        "fields": {
                            "Issue Type": jira_settings["issue_type"],
                        }
                    }
            #
            if "email" in self.dast_settings.get("reporters_checked", list()):
                project_secrets = get_project_hidden_secrets(self.project_id)
                if "smtp" in project_secrets:
                    email_settings = loads(project_secrets["smtp"])
                    reporters_config["email"] = {
                        "server": email_settings["smtp_host"],
                        "port": email_settings["smtp_port"],
                        "login": email_settings["smtp_user"],
                        "password": email_settings["smtp_password"],
                        "mail_to": self.dast_settings.get("email_recipients", ""),
                    }
                    reporters_config["html"] = {
                        "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.html",
                    }
            #
            if "ado" in self.sast_settings.get("reporters_checked", list()):
                project_secrets = get_project_hidden_secrets(self.project_id)
                if "ado" in project_secrets:
                    reporters_config["ado"] = loads(project_secrets["ado"])

            # Thresholds
            tholds = {}
            if thresholds and any(int(thresholds[key]) > -1 for key in thresholds.keys()):

                for key, value in thresholds.items():
                    if int(value) > -1:
                        tholds[key.capitalize()] = int(value)
            #
            dusty_config = {
                "config_version": 2,
                "suites": {
                    "dast": {
                        "settings": {
                            "project_name": self.dast_settings.get("project_name"),
                            "project_description": self.name,
                            "environment_name": "target",
                            "testing_type": "DAST",
                            "scan_type": "full",
                            "build_id": self.test_uid,
                            "dast": global_dast_settings
                        },
                        "scanners": {
                            "dast": scanners_config
                        },
                        "processing": {
                            "min_severity_filter": {
                                "severity": "Info"
                            },
                            "quality_gate": {
                                "thresholds": tholds
                            },
                            "false_positive": {
                                "galloper": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
                                "project_id": f"{self.project_id}",
                                "token": unsecret("{{secret.auth_token}}", project_id=self.project_id)
                            }
                        },
                        "reporters": reporters_config
                    }
                }
            }
            #
            return dusty_config
        #
        job_type = "dast"
        container = f"getcarrier/{job_type}:{CURRENT_RELEASE}"
        parameters = {
            "cmd": f"run -b galloper:{job_type}_{self.test_uid} -s {job_type}",
            "GALLOPER_URL": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
            "GALLOPER_PROJECT_ID": f"{self.project_id}",
            "GALLOPER_AUTH_TOKEN": unsecret("{{secret.auth_token}}", project_id=self.project_id),
        }
        cc_env_vars = {
            "REDIS_HOST": unsecret("{{secret.redis_host}}", project_id=self.project_id),
            "REDIS_PASSWORD": unsecret("{{secret.redis_password}}", project_id=self.project_id),
        }
        concurrency = 1
        #
        if output == "docker":
            return f"docker run --rm -i -t " \
                   f"-e project_id={self.project_id} " \
                   f"-e galloper_url={unsecret('{{secret.galloper_url}}', project_id=self.project_id)} " \
                   f"-e token=\"{unsecret('{{secret.auth_token}}', project_id=self.project_id)}\" " \
                   f"getcarrier/control_tower:latest " \
                   f"-tid {self.test_uid}"
        if output == "cc":
            execution_json = {
                "job_name": self.name,
                "job_type": job_type,
                "concurrency": concurrency,
                "container": container,
                "execution_params": dumps(parameters),
                "cc_env_vars": cc_env_vars,
            }
            if "quality" in self.dast_settings.get("reporters_checked", list()):
                execution_json["quality_gate"] = "True"
            return execution_json
        #
        return ""

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        test_param = super().to_json()
        for key in exclude_fields:
            if key in test_param.keys():
                del test_param[key]
        return test_param


class SecurityTestsSAST(AbstractBaseMixin, Base):
    """ Security Tests: SAST """
    __tablename__ = "security_tests_sast"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String(128), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    sast_settings = Column(JSON)

    def insert(self):
        if not self.test_uid:
            self.test_uid = str(uuid4())
        #
        super().insert()
        #
        project = Project.query.get_or_404(self.project_id)
        minio_client = MinioClient(project=project)
        minio_client.create_bucket(bucket="sast")

    def configure_execution_json(self, output="cc", execution=False, thresholds={}):
        """ Create configuration for execution """
        #
        if output == "dusty":
            #
            global_sast_settings = dict()
            global_sast_settings["max_concurrent_scanners"] = 1
            if "toolreports" in self.sast_settings.get("reporters_checked", list()):
                global_sast_settings["save_intermediates_to"] = "/tmp/intermediates"
            #
            actions_config = dict()
            if self.sast_settings.get("sast_target_type") == "target_git":
                actions_config["git_clone"] = {
                    "source": self.sast_settings.get("sast_target_repo"),
                    "target": "/tmp/code"
                }
                if self.sast_settings.get("sast_target_repo_user") != "":
                    actions_config["git_clone"]["username"] = unsecret(self.sast_settings.get("sast_target_repo_user"), project_id=self.project_id)
                if self.sast_settings.get("sast_target_repo_pass") != "":
                    actions_config["git_clone"]["password"] = unsecret(self.sast_settings.get("sast_target_repo_pass"), project_id=self.project_id)
                if self.sast_settings.get("sast_target_repo_key") != "":
                    actions_config["git_clone"]["key_data"] = unsecret(self.sast_settings.get("sast_target_repo_key"), project_id=self.project_id)
            if self.sast_settings.get("sast_target_type") == "target_galloper_artifact":
                actions_config["galloper_artifact"] = {
                    "bucket": self.sast_settings.get("sast_target_artifact_bucket"),
                    "object": self.sast_settings.get("sast_target_artifact"),
                    "target": "/tmp/code",
                    "delete": False
                }
            if self.sast_settings.get("sast_target_type") == "target_code_path":
                actions_config["galloper_artifact"] = {
                    "bucket": "sast",
                    "object": f"{self.test_uid}.zip",
                    "target": "/tmp/code",
                    "delete": True
                }
            #
            scanners_config = dict()
            scanners_config[self.sast_settings.get("language")] = {
                "code": "/tmp/code"
            }
            if "composition" in self.sast_settings.get("options_checked", list()):
                scanners_config["dependencycheck"] = {
                    "comp_path": "/tmp/code",
                    "comp_opts": "--enableExperimental"
                }
            if "secretscan" in self.sast_settings.get("options_checked", list()):
                scanners_config["gitleaks"] = {
                    "code": "/tmp/code"
                }
            #
            reporters_config = dict()
            reporters_config["galloper"] = {
                "url": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
                "project_id": f"{self.project_id}",
                "token": unsecret("{{secret.auth_token}}", project_id=self.project_id),
            }
            if "toolreports" in self.sast_settings.get("reporters_checked", list()):
                reporters_config["galloper_tool_reports"] = {
                    "bucket": "sast",
                    "object": f"{self.test_uid}_tool_reports.zip",
                    "source": "/tmp/intermediates",
                }
            if "quality" in self.sast_settings.get("reporters_checked", list()):
                reporters_config["galloper_junit_report"] = {
                    "bucket": "sast",
                    "object": f"{self.test_uid}_junit_report.xml",
                }
                reporters_config["galloper_quality_gate_report"] = {
                    "bucket": "sast",
                    "object": f"{self.test_uid}_quality_gate_report.json",
                }
                reporters_config["junit"] = {
                    "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.xml",
                }
            #
            if "jira" in self.sast_settings.get("reporters_checked", list()):
                project_secrets = get_project_hidden_secrets(self.project_id)
                if "jira" in project_secrets:
                    jira_settings = loads(project_secrets["jira"])
                    reporters_config["jira"] = {
                        "url": jira_settings["jira_url"],
                        "username": jira_settings["jira_login"],
                        "password": jira_settings["jira_password"],
                        "project": jira_settings["jira_project"],
                        "fields": {
                            "Issue Type": jira_settings["issue_type"],
                        }
                    }
            #
            if "email" in self.sast_settings.get("reporters_checked", list()):
                project_secrets = get_project_hidden_secrets(self.project_id)
                if "smtp" in project_secrets:
                    email_settings = loads(project_secrets["smtp"])
                    reporters_config["email"] = {
                        "server": email_settings["smtp_host"],
                        "port": email_settings["smtp_port"],
                        "login": email_settings["smtp_user"],
                        "password": email_settings["smtp_password"],
                        "mail_to": self.sast_settings.get("email_recipients", ""),
                    }
                    reporters_config["html"] = {
                        "file": "/tmp/{project_name}_{testing_type}_{build_id}_report.html",
                    }
            #
            if "ado" in self.sast_settings.get("reporters_checked", list()):
                project_secrets = get_project_hidden_secrets(self.project_id)
                if "ado" in project_secrets:
                    reporters_config["ado"] = loads(project_secrets["ado"])

            # Thresholds
            tholds = {}
            if thresholds and any(int(thresholds[key]) > -1 for key in thresholds.keys()):
                for key, value in thresholds.items():
                    if int(value) > -1:
                        tholds[key.capitalize()] = int(value)
            #
            dusty_config = {
                "config_version": 2,
                "suites": {
                    "sast": {
                        "settings": {
                            "project_name": self.sast_settings.get("project_name"),
                            "project_description": self.name,
                            "environment_name": "target",
                            "testing_type": "SAST",
                            "scan_type": "full",
                            "build_id": self.test_uid,
                            "sast": global_sast_settings
                        },
                        "actions": actions_config,
                        "scanners": {
                            "sast": scanners_config
                        },
                        "processing": {
                            "min_severity_filter": {
                                "severity": "Info"
                            },
                            "quality_gate": {
                                "thresholds": tholds
                            },
                            "false_positive": {
                                "galloper": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
                                "project_id": f"{self.project_id}",
                                "token": unsecret("{{secret.auth_token}}", project_id=self.project_id)
                            }
                        },
                        "reporters": reporters_config
                    }
                }
            }
            #
            return dusty_config
        #
        job_type = "sast"
        container = f"getcarrier/{job_type}:{CURRENT_RELEASE}"
        parameters = {
            "cmd": f"run -b galloper:{job_type}_{self.test_uid} -s {job_type}",
            "GALLOPER_URL": unsecret("{{secret.galloper_url}}", project_id=self.project_id),
            "GALLOPER_PROJECT_ID": f"{self.project_id}",
            "GALLOPER_AUTH_TOKEN": unsecret("{{secret.auth_token}}", project_id=self.project_id),
        }
        if self.sast_settings.get("sast_target_type") == "target_code_path":
            parameters["code_path"] = self.sast_settings.get("sast_target_code")
        cc_env_vars = {
            "REDIS_HOST": unsecret("{{secret.redis_host}}", project_id=self.project_id),
            "REDIS_PASSWORD": unsecret("{{secret.redis_password}}", project_id=self.project_id),
        }
        concurrency = 1
        #
        if output == "docker":
            docker_run = f"docker run --rm -i -t"
            if self.sast_settings.get("sast_target_type") == "target_code_path":
                docker_run = f"docker run --rm -i -t -v \"{self.sast_settings.get('sast_target_code')}:/code\""
            return f"{docker_run} " \
                   f"-e project_id={self.project_id} " \
                   f"-e galloper_url={unsecret('{{secret.galloper_url}}', project_id=self.project_id)} " \
                   f"-e token=\"{unsecret('{{secret.auth_token}}', project_id=self.project_id)}\" " \
                   f"getcarrier/control_tower:latest " \
                   f"-tid {self.test_uid}"
        if output == "cc":
            execution_json = {
                "job_name": self.name,
                "job_type": job_type,
                "concurrency": concurrency,
                "container": container,
                "execution_params": dumps(parameters),
                "cc_env_vars": cc_env_vars,
            }
            if "quality" in self.sast_settings.get("reporters_checked", list()):
                execution_json["quality_gate"] = "True"
            return execution_json
        #
        return ""

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        test_param = super().to_json()
        for key in exclude_fields:
            if key in test_param.keys():
                del test_param[key]
        return test_param
