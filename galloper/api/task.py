from json import dumps
from flask import request
from flask_restful import Resource
from sqlalchemy import and_

from werkzeug.exceptions import Forbidden
from werkzeug.datastructures import FileStorage

from galloper.api.base import get, create_task, run_task
from galloper.constants import allowed_file, POST_PROCESSOR_PATH, CONTROL_TOWER_PATH, APP_HOST
from galloper.data_utils.file_utils import File
from galloper.database.models.task import Task
from galloper.database.models.task_results import Results
from galloper.database.models.project import Project
from galloper.database.models.project_quota import ProjectQuota
from galloper.utils.api_utils import build_req_parser, str2bool
from galloper.dal.vault import unsecret
from galloper.dal.vault import get_project_hidden_secrets, set_project_hidden_secrets


class TasksApi(Resource):
    _get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args")
    )

    _post_rules = (
        dict(name="file", type=FileStorage, required=False, location='files'),
        dict(name="url", type=str, required=False, location='form'),
        dict(name="funcname", type=str, location='form'),
        dict(name="invoke_func", type=str, location='form'),
        dict(name="runtime", type=str, location='form'),
        dict(name="env_vars", type=str, location='form')
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)
        self.post_parser = build_req_parser(rules=self._post_rules)

    def get(self, project_id: int):
        args = self.get_parser.parse_args(strict=False)
        reports = []
        total, res = get(project_id, args, Task)
        for each in res:
            reports.append(each.to_json())
        return {"total": total, "rows": reports}

    def post(self, project_id: int):
        args = self.post_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        if args.get("file"):
            file = args["file"]
            if file.filename == "":
                return {"message": "file not selected", "code": 400}, 400
        elif args.get("url"):
            file = File(args.get("url"))
        else:
            return {"message": "Task file is not specified", "code": 400}, 400

        if file and allowed_file(file.filename):
            if not ProjectQuota.check_quota(project_id=project.id, quota='tasks_count'):
                raise Forbidden(description="The number of tasks allowed in the project has been exceeded")
        task_id = create_task(project, file, args).task_id
        return {"file": task_id, "code": 0}, 200


class TaskApi(Resource):
    _get_rules = (
        dict(name="exec", type=str2bool, default=False, location="args"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)

    def get(self, project_id: int, task_id: str):
        args = self.get_parser.parse_args(strict=False)
        task = Task.query.filter_by(task_id=task_id).first()
        project = Project.get_or_404(project_id)
        if args.get("exec"):
            return unsecret(task.to_json(), project_id=project.id)
        return task.to_json()

    def post(self, project_id: int, task_id: str):
        task = Task.query.filter_by(task_id=task_id).first()
        project = Project.get_or_404(project_id)
        event = request.get_json()
        return run_task(project.id, event, task.task_id)


class TaskActionApi(Resource):
    _get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args")
    )

    result_rules = (
        dict(name="ts", type=int, location="json"),
        dict(name="results", type=str, location="json"),
        dict(name="stderr", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._result_parser = build_req_parser(rules=self.result_rules)
        self.get_parser = build_req_parser(rules=self._get_rules)

    def get(self, task_id, action):
        task = Task.query.filter_by(task_id=task_id).first()
        if action in ("suspend", "delete", "activate"):
            getattr(task, action)()
        if action == "results":
            args = self.get_parser.parse_args(strict=False)
            reports = []
            total, res = get(task.project_id, args, Results, additional_filter={"task_id": task_id})
            for each in res:
                reports.append(each.to_json())
            return {"total": total, "rows": reports}
        return {"message": "Done", "code": 200}

    def post(self, task_id, action):
        task = Task.query.filter_by(task_id=task_id).first()
        project_id = task.project_id
        if action == "edit":
            for key, value in request.form.items():
                if key in ["id", "task_id", "zippath", "last_run"]:
                    continue
                elem = getattr(task, key, None)
                if value in ["None", "none", ""]:
                    value = None
                if elem != value:
                    setattr(task, key, value)
                task.commit()
        elif action == "results":
            data = self._result_parser.parse_args(strict=False)
            task.set_last_run(data["ts"])
            result = Results(task_id=task_id, project_id=project_id,
                             ts=data["ts"], results=data["results"],
                             log=data["stderr"])
            result.insert()
        return {"message": "Ok", "code": 201}


class TaskUpgradeApi(Resource):
    _get_rules = (dict(name="name", type=str, location="args"),)

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._result_parser = build_req_parser(rules=self.result_rules)
        self.get_parser = build_req_parser(rules=self._get_rules)

    def get(self, project_id):
        project = Project.get_or_404(project_id)
        args = self.get_parser.parse_args(strict=False)
        if args['name'] not in ['post_processor', 'control_tower']:
            return {"message": "go away", "code": 400}, 400
        task = Task.query.filter(and_(Task.project_id == project_id, Task.task_name == args['name'])).first()
        task.delete()
        if args['name'] == 'post_processor':
            pp_args = {
                "funcname": "post_processor",
                "invoke_func": "lambda_function.lambda_handler",
                "runtime": "Python 3.7",
                "env_vars": dumps({})
            }
            pp = create_task(project, File(POST_PROCESSOR_PATH), pp_args)
            secrets = get_project_hidden_secrets(project.id)
            secrets["post_processor"] = f'{APP_HOST}{pp.webhook}'
            secrets["post_processor_id"] = pp.task_id
            set_project_hidden_secrets(project.id, secrets)
        elif args['name'] == 'control_tower':
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
            secrets = get_project_hidden_secrets(project.id)
            secrets["control_tower_id"] = cc.task_id
            set_project_hidden_secrets(project.id, secrets)
        return {"message": "Done", "code": 200}
