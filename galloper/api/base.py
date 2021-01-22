import operator

from json import loads
from uuid import uuid4
from datetime import datetime
from time import mktime
from json import dumps
from requests import post
from sqlalchemy import and_
from galloper.database.models.task import Task
from galloper.database.models.project import Project
from galloper.database.models.statistic import Statistic
from galloper.database.models.project_quota import ProjectQuota
from galloper.processors.minio import MinioClient
from galloper.constants import JOB_CONTAINER_MAPPING, APP_HOST, RABBIT_USER, RABBIT_PASSWORD, RABBIT_PORT,\
    RABBIT_QUEUE_NAME, RABBIT_HOST
from galloper.dal.vault import get_project_secrets, unsecret, get_project_hidden_secrets

from werkzeug.exceptions import Forbidden
from werkzeug.utils import secure_filename

from arbiter import Arbiter
import docker


def _calcualte_limit(limit, total):
    return len(total) if limit == 'All' else limit


def get(project_id, args, data_model, additional_filter=None):
    project = Project.get_or_404(project_id)
    limit_ = args.get("limit")
    offset_ = args.get("offset")
    if args.get("sort"):
        sort_rule = getattr(getattr(data_model, args["sort"]), args["order"])()
    else:
        sort_rule = data_model.id.desc()
    filter_ = list()
    filter_.append(operator.eq(data_model.project_id, project.id))
    if additional_filter:
        for key, value in additional_filter.items():
            filter_.append(operator.eq(getattr(data_model, key), value))
    if args.get('filter'):
        for key, value in loads(args.get("filter")).items():
            filter_.append(operator.eq(getattr(data_model, key), value))
    filter_ = and_(*tuple(filter_))
    total = data_model.query.order_by(sort_rule).filter(filter_).count()
    res = data_model.query.filter(filter_).order_by(sort_rule).limit(
        _calcualte_limit(limit_, total)).offset(offset_).all()
    return total, res


def compile_tests(project_id, file_name, runner):
    client = docker.from_env()
    container_name = JOB_CONTAINER_MAPPING.get(runner)["container"]
    secrets = get_project_secrets(project_id)
    env_vars = {"artifact": file_name, "bucket": "tests", "galloper_url": secrets["galloper_url"],
                "token": secrets["auth_token"], "project_id": project_id, "compile": "true"}
    client.containers.run(container_name, stderr=True, remove=True, environment=env_vars, tty=True, user='0:0')


def upload_file(bucket, f, project, create_if_not_exists=True):
    name = f.filename
    content = f.read()
    f.seek(0, 2)
    file_size = f.tell()
    try:
        f.remove()
    except:
        pass
    storage_space_quota = project.get_storage_space_quota()
    statistic = Statistic.query.filter_by(project_id=project.id).first().to_json()
    if storage_space_quota != -1 and statistic['storage_space'] + file_size > storage_space_quota * 1000000:
        raise Forbidden(description="The storage space limit allowed in the project has been exceeded")
    if create_if_not_exists:
        if bucket not in MinioClient(project=project).list_bucket():
            MinioClient(project=project).create_bucket(bucket)
    MinioClient(project=project).upload_file(bucket, content, name)


def create_task(project, file, args):
    filename = str(uuid4())
    filename = secure_filename(filename)
    upload_file(bucket="tasks", f=file, project=project)
    task = Task(
        task_id=filename,
        project_id=project.id,
        zippath=f"tasks/{file.filename}",
        task_name=args.get("funcname"),
        task_handler=args.get("invoke_func"),
        runtime=args.get("runtime"),
        env_vars=args.get("env_vars")
    )
    task.insert()
    return task


def update_task(task_id, env_vars):
    task = Task.query.filter(and_(Task.task_id == task_id)).first()
    task.env_vars = env_vars
    task.commit()


def run_task(project_id, event, task_id=None):
    secrets = get_project_secrets(project_id)
    if "control_tower_id" not in secrets:
        secrets = get_project_hidden_secrets(project_id)
    task_id = task_id if task_id else secrets["control_tower_id"]
    task = Task.query.filter(and_(Task.task_id == task_id)).first().to_json()
    check_tasks_quota(task)
    statistic = Statistic.query.filter(Statistic.project_id == task['project_id']).first()
    setattr(statistic, 'tasks_executions', Statistic.tasks_executions + 1)
    statistic.commit()
    arbiter = get_arbiter()
    task_kwargs = {"task": unsecret(task, project_id=project_id),
                   "event": unsecret(event, project_id=project_id),
                   "galloper_url": unsecret("{{secret.galloper_url}}", project_id=task['project_id']),
                   "token": unsecret("{{secret.auth_token}}", project_id=task['project_id'])}
    arbiter.apply("execute_lambda", queue=RABBIT_QUEUE_NAME, task_kwargs=task_kwargs)
    arbiter.close()
    return {"message": "Accepted", "code": 200, "task_id": task_id}


def get_arbiter():
    arbiter = Arbiter(host=RABBIT_HOST, port=RABBIT_PORT, user=RABBIT_USER, password=RABBIT_PASSWORD)
    return arbiter


def check_tasks_quota(task):
    if not ProjectQuota.check_quota(project_id=task['project_id'], quota='tasks_executions'):
        data = {"ts": int(mktime(datetime.utcnow().timetuple())), 'results': 'Forbidden',
                'stderr': "The number of task executions allowed in the project has been exceeded"}

        headers = {
            "Content-Type": "application/json",
            "Token": task['token']
        }
        auth_token = unsecret("{{secret.auth_token}}", project_id=task['project_id'])
        if auth_token:
            headers['Authorization'] = f'bearer {auth_token}'
        post(f'{APP_HOST}/api/v1/task/{task["task_id"]}/results', headers=headers, data=dumps(data))
        raise Forbidden(description="The number of task executions allowed in the project has been exceeded")
