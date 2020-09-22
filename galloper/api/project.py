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

from json import dumps
from typing import Optional, Union, Tuple
from flask import current_app
from flask_restful import Resource
from sqlalchemy import and_, or_

from galloper.database.models.project import Project
from galloper.database.models.statistic import Statistic
from galloper.database.models import project_quota
from galloper.utils.api_utils import build_req_parser
from galloper.utils.auth import SessionProject, SessionUser
from galloper.dal.vault import initialize_project_space, remove_project_space, set_project_secrets,\
    set_project_hidden_secrets
from galloper.api.base import create_task
from galloper.data_utils.file_utils import File
from galloper.constants import (POST_PROCESSOR_PATH, CONTROL_TOWER_PATH, APP_IP, APP_HOST,
                                EXTERNAL_LOKI_HOST, INFLUX_PORT, LOKI_PORT, REDIS_PASSWORD)

from datetime import datetime
from galloper.utils.auth import only_users_projects, superadmin_required


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
        dict(name="package", type=str, default='custom', location="json"),
        dict(name="perf_tests_limit", type=int, default=100, location="json"),
        dict(name="ui_perf_tests_limit", type=int, default=100, location="json"),
        dict(name="sast_scans_limit", type=int, default=100, location="json"),
        dict(name="dast_scans_limit", type=int, default=100, location="json"),
        dict(name="tasks_count_limit", type=int, default=3, location="json"),
        dict(name="task_executions_limit", type=int, default=200, location="json"),
        dict(name="storage_space_limit", type=int, default=100, location="json"),
        dict(name="data_retention_limit", type=int, default=30, location="json")
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
        allowed_project_ids = only_users_projects()
        _filter = None
        if "all" not in allowed_project_ids:
            _filter = Project.id.in_(allowed_project_ids)
        if project_id:
            project = Project.get_or_404(project_id)
            return project.to_json(exclude_fields=Project.API_EXCLUDE_FIELDS), 200
        elif search_:
            filter_ = Project.name.ilike(f"%{search_}%")
            if _filter is not None:
                filter_ = and_(_filter, filter_)
            projects = Project.query.filter(filter_).limit(limit_).offset(offset_).all()
        else:
            if _filter is not None:
                projects = Project.query.filter(_filter).limit(limit_).offset(offset_).all()
            else:
                projects = Project.query.limit(limit_).offset(offset_).all()

        return [project.to_json(exclude_fields=Project.API_EXCLUDE_FIELDS) for project in projects], 200

    @superadmin_required
    def post(self, project_id: Optional[int] = None) -> Tuple[dict, int]:
        data = self._parser_post.parse_args()
        name_ = data["name"]
        owner_ = data["owner"]
        package = data["package"].lower()
        dast_enabled_ = False if data["dast_enabled"] == "disabled" else True
        sast_enabled_ = False if data["sast_enabled"] == "disabled" else True
        performance_enabled_ = False if data["performance_enabled"] == "disabled" else True
        perf_tests_limit = data["perf_tests_limit"]
        ui_perf_tests_limit = data["ui_perf_tests_limit"]
        sast_scans_limit = data["sast_scans_limit"]
        dast_scans_limit = data["dast_scans_limit"]
        tasks_count_limit = data["tasks_count_limit"]
        task_executions_limit = data["task_executions_limit"]
        storage_space_limit = data["storage_space_limit"]
        data_retention_limit = data["data_retention_limit"]

        project = Project(
            name=name_,
            dast_enabled=dast_enabled_,
            project_owner=owner_,
            sast_enabled=sast_enabled_,
            performance_enabled=performance_enabled_,
            package=package
        )
        project_secrets = {}
        project_hidden_secrets = {}
        project.insert()
        SessionProject.set(project.id)  # Looks weird, sorry :D
        if package == "custom":
            getattr(project_quota, "custom")(project.id, perf_tests_limit, ui_perf_tests_limit, sast_scans_limit,
                                             dast_scans_limit, -1, storage_space_limit, data_retention_limit,
                                             tasks_count_limit, task_executions_limit)
        else:
            getattr(project_quota, package)(project.id)

        statistic = Statistic(
            project_id=project.id,
            start_time=str(datetime.utcnow()),
            performance_test_runs=0,
            sast_scans=0,
            dast_scans=0,
            ui_performance_test_runs=0,
            public_pool_workers=0,
            tasks_executions=0
        )
        statistic.insert()

        pp_args = {
            "funcname": "post_processor",
            "invoke_func": "lambda_function.lambda_handler",
            "runtime": "Python 3.7",
            "env_vars": dumps({})
        }
        pp = create_task(project, File(POST_PROCESSOR_PATH), pp_args)
        cc_args = {
            "funcname": "control_tower",
            "invoke_func": "lambda.handler",
            "runtime": "Python 3.7",
            "env_vars": dumps({
                "REDIS_HOST": "{{secret.redis_host}}",
                "REDIS_DB": 1,
                "token": "{{secret.auth_token}}",
                "galloper_url": "{{secret.galloper_url}}",
                "GALLOPER_WEB_HOOK": '{{secret.post_processor}}',
                "project_id": '{{secret.project_id}}',
                "loki_host": '{{secret.loki_host}}'
            })
        }
        cc = create_task(project, File(CONTROL_TOWER_PATH), cc_args)

        project_secrets["galloper_url"] = APP_HOST
        project_secrets["project_id"] = project.id
        project_hidden_secrets["post_processor"] = f'{APP_HOST}{pp.webhook}'
        project_hidden_secrets["post_processor_id"] = pp.task_id
        project_hidden_secrets["redis_host"] = APP_IP
        project_hidden_secrets["loki_host"] = EXTERNAL_LOKI_HOST.replace("https://", "http://")
        project_hidden_secrets["influx_ip"] = APP_IP
        project_hidden_secrets["influx_port"] = INFLUX_PORT
        project_hidden_secrets["loki_port"] = LOKI_PORT
        project_hidden_secrets["redis_password"] = REDIS_PASSWORD
        project_hidden_secrets["control_tower_id"] = cc.task_id
        project_vault_data = {
            "auth_role_id": "",
            "auth_secret_id": ""
        }
        try:
            project_vault_data = initialize_project_space(project.id)
        except:
            current_app.logger.warning("Vault is not configured")
        project.secrets_json = {
            "vault_auth_role_id": project_vault_data["auth_role_id"],
            "vault_auth_secret_id": project_vault_data["auth_secret_id"],
        }
        project.commit()
        set_project_secrets(project.id, project_secrets)
        set_project_hidden_secrets(project.id, project_hidden_secrets)
        return {"message": f"Project was successfully created"}, 200

    def put(self, project_id: Optional[int] = None) -> Tuple[dict, int]:
        data = self._parser_post.parse_args()
        if not project_id:
            return {"message": "Specify project id"}, 400
        project = Project.get_or_404(project_id)
        project.name = data["name"]
        project.project_owner = data["owner"]
        package = data["package"].lower()
        project.dast_enabled = False if data["dast_enabled"] == "disabled" else True
        project.sast_enabled = False if data["sast_enabled"] == "disabled" else True
        project.performance_enabled = False if data["performance_enabled"] == "disabled" else True
        project.package = package
        project.commit()
        if package == "custom":
            getattr(project_quota, "custom")(project.id, data["perf_tests_limit"], data["ui_perf_tests_limit"],
                                             data["sast_scans_limit"], data["dast_scans_limit"], -1,
                                             data["storage_space_limit"], data["data_retention_limit"],
                                             data["tasks_count_limit"], data["task_executions_limit"])
        else:
            getattr(project_quota, package)(project.id)

        return project.to_json(exclude_fields=Project.API_EXCLUDE_FIELDS)

    def delete(self, project_id: int) -> Tuple[dict, int]:
        Project.apply_full_delete_by_pk(pk=project_id)
        remove_project_space(project_id)
        return {"message": f"Project with id {project_id} was successfully deleted"}, 200


class ProjectSessionAPI(Resource):
    post_rules = (
        dict(name="username", type=str, required=True, location="json"),
        dict(name="groups", type=list, required=True, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: Optional[int] = None) -> Tuple[dict, int]:
        if not project_id:
            project_id = SessionProject.get()
        if project_id:
            project = Project.get_or_404(project_id)
            return project.to_json(exclude_fields=Project.API_EXCLUDE_FIELDS), 200
        return {"message": "No project selected in session"}, 404

    def post(self, project_id: Optional[int] = None) -> Tuple[dict, int]:
        args = self._parser_post.parse_args()
        SessionUser.set(dict(username=args["username"], groups=args.get("groups")))
        if project_id:
            project = Project.get_or_404(project_id)
            SessionProject.set(project.id)
            return {"message": f"Project with id {project.id} was successfully selected"}, 200
        return {"message": "user session configured"}, 200

    def delete(self, project_id: int) -> Tuple[dict, int]:
        project = Project.get_or_404(project_id)
        if SessionProject.get() == project.id:
            SessionProject.pop()
        return {"message": f"Project with id {project.id} was successfully unselected"}, 200
