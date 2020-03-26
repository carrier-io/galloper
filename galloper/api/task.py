from flask import request
from flask_restful import Resource
from galloper.database.models.task import Task
from galloper.database.models.task_results import Results
from galloper.utils.api_utils import build_req_parser


class TaskActionApi(Resource):
    result_rules = (
        dict(name="ts", type=int, location="json"),
        dict(name="results", type=str, location="json"),
        dict(name="stderr", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._result_parser = build_req_parser(rules=self.result_rules)

    def get(self, task_id, action):
        task = Task.query.filter_by(task_id=task_id).first()
        if action in ("suspend", "delete", "activate"):
            getattr(task, action)()
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
