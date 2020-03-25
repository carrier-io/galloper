from sqlalchemy import or_, and_
from flask import request
from flask_restful import Resource
from galloper.database.models.task import Task
from galloper.database.models.project import Project
from galloper.database.models.task_results import Results


class TaskActionApi(Resource):
    def get(self, task_id, action):
        task = Task.query.filter(and_(Task.task_id == task_id)).first()
        if action in ("suspend", "delete", "activate"):
            getattr(task, action)()
        return {"message": "Done", "code": 200}

    def post(self, task_id, action):
        task = Task.query.filter(and_(Task.task_id == task_id)).first()
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
            data = request.get_json()
            task.set_last_run(data["ts"])
            result = Results(task_id=task_id, project_id=project_id,
                             ts=data["ts"], results=data["results"],
                             log=data["stderr"])
            result.insert()
        return {"message": "Ok", "code": 201}
