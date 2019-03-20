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

import argparse

interceptor_conf = """[supervisord]

[program:worker]
command=celery -A galloper.celeryapp worker -l info -c%s --max-tasks-per-child 1 -f /var/log/interceptor.log
autostart=true
autorestart=true
stopsignal=QUIT
stopwaitsecs=20
stopasgroup=true

[program:app]
command=app
autostart=true
autorestart=true
stopsignal=QUIT
stopwaitsecs=20
stopasgroup=true
"""


def arg_parse():
    parser = argparse.ArgumentParser(description='Supervisord Config Creator')
    parser.add_argument('-p', '--procs', type=int, default=4, help="specify amount of cores on server")
    return parser.parse_args()


def main():
    args = arg_parse()
    with open('/etc/galloper.conf', 'w') as f:
        f.write(interceptor_conf % args.procs)
