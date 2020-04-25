import os
import operator

from flask import current_app
from json import loads
from uuid import uuid4
from sqlalchemy import and_
from galloper.database.models.task import Task
from galloper.database.models.project import Project
from galloper.database.models.statistic import Statistic
from galloper.processors.minio import MinioClient

from werkzeug.exceptions import Forbidden
from werkzeug.utils import secure_filename

from botocore.exceptions import ClientError

from control_tower import run

def _calcualte_limit(limit, total):
    return len(total) if limit == 'All' else limit


def get(project_id, args, data_model):
    project = Project.query.get_or_404(project_id)
    limit_ = args.get("limit")
    offset_ = args.get("offset")
    if args.get("sort"):
        sort_rule = getattr(getattr(data_model, args["sort"]), args["order"])()
    else:
        sort_rule = data_model.id.asc()
    if not args.get('filter'):
        total = data_model.query.filter(data_model.project_id == project.id).order_by(sort_rule).count()
        res = data_model.query.filter(
            data_model.project_id == project.id
        ).order_by(sort_rule).limit(_calcualte_limit(limit_, total)).offset(offset_).all()
    else:
        filter_ = list()
        filter_.append(operator.eq(data_model.project_id, project.id))
        for key, value in loads(args.get("filter")).items():
            filter_.append(operator.eq(getattr(data_model, key), value))
        filter_ = and_(*tuple(filter_))
        total = data_model.query.order_by(sort_rule).filter(filter_).count()
        res = data_model.query.filter(filter_).order_by(sort_rule).limit(
            _calcualte_limit(limit_, total)).offset(offset_).all()
    return total, res


def upload_file(bucket, f, project, create_if_not_exists=False):
    name = f.filename
    content = f.read()
    f.seek(0, 2)
    file_size = f.tell()
    storage_space_quota = project.get_storage_space_quota()
    statistic = Statistic.query.filter_by(project_id=project.id).first().to_json()
    if storage_space_quota != -1 and statistic['storage_space'] + file_size > storage_space_quota * 1000000:
        raise Forbidden(description="The storage space limit allowed in the project has been exceeded")
    try:
        MinioClient(project=project).upload_file(bucket, content, name)
    except ClientError as err:
        if err.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
            MinioClient(project=project).create_bucket(bucket)
            MinioClient(project=project).upload_file(bucket, content, name)


def create_task(project, file, args):
    filename = str(uuid4())
    filename = secure_filename(filename)
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    app = run.connect_to_celery(1)
    celery_task = app.signature(
        "tasks.volume",
        kwargs={"task_id": filename, "file_path": current_app.config["UPLOAD_FOLDER"]}
    )
    celery_task.apply_async()
    task = Task(
        task_id=filename,
        project_id=project.id,
        zippath=filename,
        task_name=args.get("funcname"),
        task_handler=args.get("invoke_func"),
        runtime=args.get("runtime"),
        env_vars=args.get("env_vars")
    )
    task.insert()
    return task


def run_task(task_id, event):
    task = Task.query.filter(
        and_(Task.task_id == task_id)
    ).first().to_json()
    app = run.connect_to_celery(1)
    celery_task = app.signature("tasks.execute",
                                kwargs={"task": task, "event": event})
    celery_task.apply_async()
    return {"message": "Accepted", "code": 200}
