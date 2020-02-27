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

from uuid import uuid4
from galloper.models import db, BaseModel


class Task(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(80), unique=True, nullable=False)
    zippath = db.Column(db.String(80), unique=True, nullable=False)
    task_name = db.Column(db.String(80), unique=False, nullable=False)
    task_handler = db.Column(db.String(80), unique=False, nullable=False)
    runtime = db.Column(db.String(80), unique=False, nullable=False)
    schedule = db.Column(db.String(80), unique=False, nullable=True)
    next_run = db.Column(db.Integer, unique=False, nullable=True)
    webhook = db.Column(db.String(80), unique=False, nullable=True)
    last_run = db.Column(db.Integer, unique=False, nullable=True)
    status = db.Column(db.String(80), unique=False, nullable=True)
    token = db.Column(db.String(80), unique=False, nullable=True)
    func_args = db.Column(db.Text, unique=False, nullable=True)
    env_vars = db.Column(db.Text, unique=False, nullable=True)
    callback = db.Column(db.String(80), unique=False, nullable=True)

    def to_json(self):
        if self.schedule and self.schedule in ['None', 'none', '']:
            self.schedule = None
        if self.callback and self.callback in ['None', 'none', '']:
            self.callback = None
        return dict(task_id=self.task_id, task_name=self.task_name, task_handler=self.task_handler,
                    runtime=self.runtime, schedule=self.schedule, webhook=self.webhook,
                    zippath=self.zippath, last_run=self.last_run, status=self.status, token=self.token,
                    func_args=self.func_args, callback=self.callback, env_vars=self.env_vars)

    def insert(self):
        if self.schedule and self.schedule in ['None', 'none']:
            self.schedule = None
        if self.callback and self.callback in ['None', 'none']:
            self.callback = None
        if not self.webhook:
            self.webhook = f'/task/{self.task_id}'
        if not self.status:
            self.status = 'suspended'
        if not self.token:
            self.token = str(uuid4())
        if not self.func_args:
            self.func_args = "{}"
        if not self.env_vars:
            self.env_vars = "{}"
        db.session.add(self)
        db.session.commit()

    def suspend(self):
        self.status = 'suspended'
        db.session.commit()

    def activate(self):
        self.status = 'active'
        db.session.commit()

    def set_last_run(self, ts):
        self.last_run = ts
        db.session.commit()
