from json import dumps
from flask import request
from flask_restful import Resource
from sqlalchemy import and_

from werkzeug.exceptions import Forbidden
from werkzeug.datastructures import FileStorage

from galloper.api.base import get, create_task, run_task
from galloper.constants import allowed_file, POST_PROCESSOR_PATH, CONTROL_TOWER_PATH, APP_HOST, REDIS_PASSWORD, \
    APP_IP, EXTERNAL_LOKI_HOST, INFLUX_PORT, LOKI_PORT, RABBIT_USER, RABBIT_PASSWORD, INFLUX_PASSWORD, INFLUX_USER
from galloper.data_utils.file_utils import File
from galloper.database.models.task import Task
from galloper.database.models.task_results import Results
from galloper.database.models.project import Project
from galloper.database.models.project_quota import ProjectQuota
from galloper.utils.api_utils import build_req_parser, str2bool
from galloper.api.base import upload_file
from galloper.dal.vault import unsecret
from galloper.dal.vault import get_project_hidden_secrets, get_project_secrets, set_project_hidden_secrets,\
    set_project_secrets


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
        self.get_parser = build_req_parser(rules=self._get_rules)

    def create_cc_task(self, project):
        upload_file(bucket="tasks", f=File(CONTROL_TOWER_PATH), project=project)
        task = Task.query.filter(and_(Task.task_name == "control_tower", Task.project_id == project.id)).first()
        setattr(task, "zippath", "tasks/control-tower.zip")
        task.commit()

    def create_pp_task(self, project):
        upload_file(bucket="tasks", f=File(POST_PROCESSOR_PATH), project=project)
        task = Task.query.filter(and_(Task.task_name == "post_processor", Task.project_id == project.id)).first()
        setattr(task, "zippath", "tasks/post_processing.zip")
        task.commit()

    def get(self, project_id):
        project = Project.get_or_404(project_id)
        args = self.get_parser.parse_args(strict=False)
        if args['name'] not in ['post_processor', 'control_tower', 'all']:
            return {"message": "go away", "code": 400}, 400
        secrets = get_project_hidden_secrets(project.id)
        project_secrets = get_project_secrets(project.id)
        if args['name'] == 'post_processor':
            self.create_pp_task(project)
        elif args['name'] == 'control_tower':
            self.create_cc_task(project)
        elif args['name'] == 'all':
            self.create_pp_task(project)
            self.create_cc_task(project)
            project_secrets["galloper_url"] = APP_HOST
            project_secrets["project_id"] = project.id
            secrets["post_processor"] = f"{APP_HOST}/task/{secrets['post_processor_id']}"
            secrets["redis_host"] = APP_IP
            secrets["loki_host"] = EXTERNAL_LOKI_HOST.replace("https://", "http://")
            secrets["influx_ip"] = APP_IP
            secrets["influx_port"] = INFLUX_PORT
            secrets["influx_user"] = INFLUX_USER
            secrets["influx_password"] = INFLUX_PASSWORD
            secrets["loki_port"] = LOKI_PORT
            secrets["redis_password"] = REDIS_PASSWORD
            secrets["rabbit_host"] = APP_IP
            secrets["rabbit_user"] = RABBIT_USER
            secrets["rabbit_password"] = RABBIT_PASSWORD
            set_project_secrets(project.id, project_secrets)
        else:
            return {"message": "go away", "code": 400}, 400
        set_project_hidden_secrets(project.id, secrets)
        return {"message": "Done", "code": 200}
