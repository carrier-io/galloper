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

from uuid import uuid4

from sqlalchemy import Column, Integer, String, Text

from galloper.database.db_manager import Base
from galloper.database.abstract_base import AbstractBaseMixin


class Task(AbstractBaseMixin, Base):
    __tablename__ = "task"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    task_id = Column(String(128), unique=True, nullable=False)
    zippath = Column(String(128), unique=True, nullable=False)
    task_name = Column(String(128), unique=False, nullable=False)
    task_handler = Column(String(128), unique=False, nullable=False)
    runtime = Column(String(128), unique=False, nullable=False)
    schedule = Column(String(128), unique=False, nullable=True)
    next_run = Column(Integer, unique=False, nullable=True)
    webhook = Column(String(128), unique=False, nullable=True)
    last_run = Column(Integer, unique=False, nullable=True)
    status = Column(String(128), unique=False, nullable=True)
    token = Column(String(128), unique=False, nullable=True)
    func_args = Column(Text, unique=False, nullable=True)
    env_vars = Column(Text, unique=False, nullable=True)
    callback = Column(String(128), unique=False, nullable=True)

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        json_dict = super().to_json(exclude_fields=exclude_fields or ("schedule", "callback"))
        json_dict["schedule"] = self.schedule if self.schedule not in ("None", "none", "") else None
        json_dict["callback"] = self.callback if self.callback not in ("None", "none", "") else None
        return json_dict

    def insert(self):
        if self.schedule and self.schedule in ("None", "none", ""):
            self.schedule = None
        if self.callback and self.callback in ("None", "none", ""):
            self.callback = None
        if not self.webhook:
            self.webhook = f"/task/{self.task_id}"
        if not self.status:
            self.status = "suspended"
        if not self.token:
            self.token = str(uuid4())
        if not self.func_args:
            self.func_args = "{}"
        if not self.env_vars:
            self.env_vars = "{}"
        super().insert()

    def suspend(self):
        self.status = "suspended"
        self.commit()

    def activate(self):
        self.status = "active"
        self.commit()

    def set_last_run(self, ts):
        self.last_run = ts
        self.commit()
