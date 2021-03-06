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

interceptor_conf = """[supervisord]
logfile=/tmp/supervisord.log

[unix_http_server]
file=/run/supervisord.sock

[supervisorctl]
serverurl=unix:///run/supervisord.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

"""

prod = """[program:app]
command=uwsgi --wsgi-disable-file-wrapper --ini /etc/uwsgi.ini
autostart=true
autorestart=true
stopsignal=QUIT
stopwaitsecs=20
stopasgroup=true"""


dev = """[program:app]
command=app
autostart=true
autorestart=true
stopsignal=QUIT
stopwaitsecs=20
stopasgroup=true"""


def main():
    ini_file = interceptor_conf + (prod if environ.get("env", "prod") == "prod" else dev)
    with open('/etc/galloper.conf', 'w') as f:
        f.write(ini_file)
