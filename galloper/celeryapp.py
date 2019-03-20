#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import docker
from docker.types import Mount

from requests import post
from time import time
from os import mkdir, path, rename
from json import dumps
from celery import Celery
from celery.contrib.abortable import AbortableTask
from subprocess import Popen, PIPE

from galloper.constants import (REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, REDIS_USER,
                                UNZIP_DOCKERFILE, UNZIP_DOCKER_COMPOSE, APP_HOST)

app = Celery('Galloper',
             broker=f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
             backend=f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
             include=['celery'])


app.conf.update(timezone='UTC', result_expires=1800)


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
    client = docker.from_env()
    container_name = task['runtime'].lower().replace(" ", "")
    mount = Mount(type="volume", source=task['task_id'], target="/var/task")
    response = client.containers.run(f"lambci/lambda:{container_name}",
                                     command=[f"{task['task_handler']}", dumps(event)],
                                     mounts=[mount], remove=True)
    data = {"ts": int(time()), 'results': response.decode("utf-8", errors='ignore')}

    headers = {
        "Content-Type": "application/json",
        "Token": task['token']
    }
    post(f'{APP_HOST}/task/{task["task_id"]}/results', headers=headers, data=dumps(data))
    return 'Done'


def main():
    app.start()


if __name__ == '__main__':
    main()


