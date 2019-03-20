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

from os import environ

ALLOWED_EXTENSIONS = ['zip', 'py']

REDIS_USER = environ.get('REDIS_USER', '')
REDIS_PASSWORD = environ.get('REDIS_PASSWORD', 'password')
REDIS_HOST = environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = environ.get('REDIS_PORT', '6379')
REDIS_DB = environ.get('REDIS_DB', 2)
APP_HOST = environ.get('APP_HOST', 'localhost')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


UNZIP_DOCKERFILE = """FROM kubeless/unzip:latest
ADD {localfile} /tmp/{docker_path}
ENTRYPOINT ["unzip", "/tmp/{docker_path}", "-d", "/tmp/unzipped"]
"""


UNZIP_DOCKER_COMPOSE = """version: '3'
services:
  unzip:
    build: {path}
    volumes: 
      - {volume}:/tmp/unzipped
    labels:
      - 'traefik.enable=false'
    container_name: unzip-{task_id}
volumes:
  {volume}:
    external: true
"""