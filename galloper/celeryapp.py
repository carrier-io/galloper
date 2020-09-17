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

import re
from datetime import datetime
from json import dumps, loads
from os import mkdir, path, rename
from subprocess import Popen, PIPE
from time import mktime

import docker
from celery import Celery
from celery.contrib.abortable import AbortableTask
from croniter import croniter
from docker.types import Mount
from requests import post

from galloper.constants import (REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, REDIS_USER,
                                UNZIP_DOCKERFILE, UNZIP_DOCKER_COMPOSE, APP_HOST, NAME_CONTAINER_MAPPING)
from galloper.database.db_manager import db_session
from galloper.database.models.task import Task
from galloper.database.models.statistic import Statistic
from galloper.database.models.project_quota import ProjectQuota
from werkzeug.exceptions import Forbidden
from galloper.dal.vault import unsecret

app = Celery('Galloper',
             broker=f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
             backend=f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
             include=['celery'])


def get_schedule():
    result = dict()
    result['run-scheduled'] = dict(task='tasks.scheduled', schedule=60.0, args=())
    return result


app.conf.update(
    beat_schedule=get_schedule(),
    timezone='UTC',
    result_expires=1800,
    broker_transport_options={'visibility_timeout': 57600})


def run_lambda(task, event):
    client = docker.from_env()

    container_name = NAME_CONTAINER_MAPPING.get(task['runtime'])
    if not container_name:
        return f"Container {task['runtime']} is not found"
    mount = Mount(type="volume", source=task['task_id'], target="/var/task")
    env_vars = loads(task.get("env_vars", "{}"))
    response = client.containers.run(f"lambci/{container_name}",
                                     command=[f"{task['task_handler']}", dumps(event)],
                                     mounts=[mount], stderr=True, remove=True,
                                     environment=env_vars)
    log = response.decode("utf-8", errors='ignore')
    if container_name == "lambda:python3.7":
        results = re.findall(r'({.+?})', log)[-1]
    else:
        # TODO: magic of 2 enters is very flaky, Need to think on how to workaround, probably with specific logging
        results = log.split("\n\n")[1]

    data = {"ts": int(mktime(datetime.utcnow().timetuple())), 'results': results, 'stderr': log}

    headers = {
        "Content-Type": "application/json",
        "Token": task['token']
    }
    auth_token = unsecret("{{secret.auth_token}}", project_id=task['project_id'])
    if auth_token:
        headers['Authorization'] = f'bearer {auth_token}'
    post(f'{APP_HOST}/api/v1/task/{task["task_id"]}/results', headers=headers, data=dumps(data))
    return results


@app.task(name="tasks.volume", bind=True, acks_late=True, base=AbortableTask)
def zip_to_volume(self, task_id, file_path, *args, **kwargs):
    client = docker.from_env()
    client.volumes.create(task_id)
    mkdir(f'/tmp/{task_id}')
    rename(path.join(file_path, task_id), f'/tmp/{task_id}/{task_id}')
    with open(f"/tmp/{task_id}/Dockerfile", 'w') as f:
        f.write(UNZIP_DOCKERFILE.format(localfile=task_id, docker_path=f'{task_id}.zip'))
    with open(f"/tmp/{task_id}/docker-compose.yaml", 'w') as f:
        f.write(UNZIP_DOCKER_COMPOSE.format(path=f"/tmp/{task_id}",
                                            volume=task_id, task_id=task_id))
    cmd = ['docker-compose', 'up']
    popen = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, cwd=f"/tmp/{task_id}")
    popen.communicate()
    cmd = ['docker-compose', 'down', '--rmi', 'all']
    popen = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, cwd=f"/tmp/{task_id}")
    return popen.communicate()


@app.task(name="tasks.execute", bind=True, acks_late=True, base=AbortableTask)
def execute_lambda(self, task, event, *args, **kwargs):
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
    statistic = db_session.query(Statistic).filter(Statistic.project_id == task['project_id']).first()
    setattr(statistic, 'tasks_executions', Statistic.tasks_executions + 1)
    statistic.commit()
    res = run_lambda(task, event)
    if task['callback']:
        event['result'] = res
        task = db_session.query(Task).filter(Task.task_id == task['callback'])[0].to_json()
        execute_lambda.apply_async(kwargs=dict(task=task, event=event))
    return res


def calculate_next_run(task):
    itr = croniter(task.schedule, datetime.utcnow())
    next_run = (mktime(itr.get_next(datetime).timetuple()))
    return int(next_run)


@app.task(name="tasks.scheduled", bind=True, acks_late=True)
def scan_tasks(self, *args, **kwargs):
    next_run = 0
    for task in db_session.query(Task).filter(Task.schedule != None):
        if task.last_run is None or task.next_run is None or task.next_run < int(mktime(datetime.utcnow().timetuple())):
            next_run = calculate_next_run(task)
            task.next_run = next_run
            db_session.commit()
            execute_lambda.apply_async(kwargs=dict(task=task.to_json(), event=loads(task.func_args)))
    return "Schedules all what is required", int(mktime(datetime.utcnow().timetuple())), next_run


def main():
    app.start()


if __name__ == '__main__':
    main()
