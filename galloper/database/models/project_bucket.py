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

import time

from sqlalchemy import String, Column, Integer

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base, db_session


class ProjectBucket(AbstractBaseMixin, Base):
    __tablename__ = "project_bucket"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False)
    name = Column(String(256), unique=False)
    internal_bucket_name = Column(String(512), unique=False)

    def add(self) -> None:
        timestamp = int(time.time())
        self.internal_bucket_name = f"{self.project_id}{self.name}{timestamp}"
        db_session.add(self)
