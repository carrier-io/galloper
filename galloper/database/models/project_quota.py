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

from sqlalchemy import Column, Integer

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base


class ProjectQuota(AbstractBaseMixin, Base):
    __tablename__ = "project_quota"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    performance_test_runs = Column(Integer, unique=False)  # per month
    code_repositories = Column(Integer, unique=False)  # total active
    dast_scans = Column(Integer, unique=False)  # per month
    public_pool_workers = Column(Integer, unique=False)
    storage_space = Column(Integer, unique=False)
    data_retention_limit = Column(Integer, unique=False)
    tasks_limit = Column(Integer, unique=False)
