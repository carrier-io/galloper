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

from json import dumps

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text

Base = declarative_base()


class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    task_id = Column(String(80), unique=True, nullable=False)
    zippath = Column(String(80), unique=True, nullable=False)
    task_name = Column(String(80), unique=False, nullable=False)
    task_handler = Column(String(80), unique=False, nullable=False)
    runtime = Column(String(80), unique=False, nullable=False)
    schedule = Column(String(80), unique=False, nullable=True)
    next_run = Column(Integer, unique=False, nullable=True)
    webhook = Column(String(80), unique=False, nullable=True)
    last_run = Column(Integer, unique=False, nullable=True)
    status = Column(String(80), unique=False, nullable=True)
    token = Column(String(80), unique=False, nullable=True)
    func_args = Column(Text, unique=False, nullable=True)
    env_vars = Column(Text, unique=False, nullable=True)
    callback = Column(String(80), unique=False, nullable=True)

    def __repr__(self):
        return dumps(self.to_json(), indent=2)

    def to_json(self):
        if self.schedule and self.schedule in ['None', 'none', '']:
            self.schedule = None
        if self.callback and self.callback in ['None', 'none', '']:
            self.callback = None
        return dict(task_id=self.task_id, task_name=self.task_name, task_handler=self.task_handler,
                    runtime=self.runtime, schedule=self.schedule, webhook=self.webhook,
                    zippath=self.zippath, last_run=self.last_run, status=self.status, token=self.token,
                    func_args=self.func_args, callback=self.callback, next_run=self.next_run, 
                    env_vars=self.env_vars)
