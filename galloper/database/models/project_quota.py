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

from sqlalchemy import Column, Integer, String

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base


class ProjectQuota(AbstractBaseMixin, Base):
    __tablename__ = "project_quota"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    name = Column(String, unique=False, nullable=False)
    performance_test_runs = Column(Integer, unique=False)  # per month
    sast_scans = Column(Integer, unique=False)  # total active
    dast_scans = Column(Integer, unique=False)  # per month
    public_pool_workers = Column(Integer, unique=False)
    storage_space = Column(Integer, unique=False)
    data_retention_limit = Column(Integer, unique=False)
    tasks_limit = Column(Integer, unique=False)
    tasks_executions = Column(Integer, unique=False)

    def update(self, name, performance_test_runs, sast_scans, dast_scans, public_pool_workers,
               storage_space, data_retention_limit, tasks_limit, tasks_executions):
        self.name = name
        self.performance_test_runs = performance_test_runs
        self.sast_scans = sast_scans
        self.dast_scans = dast_scans
        self.public_pool_workers = public_pool_workers
        self.storage_space = storage_space
        self.data_retention_limit = data_retention_limit
        self.tasks_limit = tasks_limit
        self.tasks_executions = tasks_executions
        self.commit()


def _update_quota(name, project_id, performance_test_runs, sast_scans, dast_scans,
                  public_pool_workers, storage_space, data_retention_limit, tasks_limit,
                  tasks_executions):
    quota = ProjectQuota.query.filter_by(project_id=project_id).first()
    if quota:
        quota.update(name=name, performance_test_runs=performance_test_runs, sast_scans=sast_scans,
                     dast_scans=dast_scans, public_pool_workers=public_pool_workers,
                     storage_space=storage_space, data_retention_limit=data_retention_limit,
                     tasks_limit=tasks_limit, tasks_executions=tasks_executions)
    else:
        quota = ProjectQuota(name=name, project_id=project_id, performance_test_runs=performance_test_runs,
                             sast_scans=sast_scans, dast_scans=dast_scans, public_pool_workers=public_pool_workers,
                             storage_space=storage_space, data_retention_limit=data_retention_limit,
                             tasks_limit=tasks_limit, tasks_executions=tasks_executions)
        quota.insert()
    return quota


def basic(project_id):
    return _update_quota(name="basic",
                         project_id=project_id,
                         performance_test_runs=10,
                         sast_scans=10,
                         dast_scans=0,
                         public_pool_workers=1,
                         storage_space=100,
                         data_retention_limit=30,
                         tasks_limit=3,
                         tasks_executions=300)


def startup(project_id):
    return _update_quota(name="startup",
                         project_id=project_id,
                         performance_test_runs=100,
                         sast_scans=100,
                         dast_scans=20,
                         public_pool_workers=3,
                         storage_space=500,
                         data_retention_limit=90,
                         tasks_limit=5,
                         tasks_executions=1000)


def professional(project_id):
    return _update_quota(name="professional",
                         project_id=project_id,
                         performance_test_runs=1000,
                         sast_scans=1000,
                         dast_scans=100,
                         public_pool_workers=5,
                         storage_space=1024,
                         data_retention_limit=365,
                         tasks_limit=10,
                         tasks_executions=10000)


def enterprise(project_id):
    return _update_quota(name="enterprise",
                         project_id=project_id,
                         performance_test_runs=-1,
                         sast_scans=-1,
                         dast_scans=-1,
                         public_pool_workers=-1,
                         storage_space=-1,
                         data_retention_limit=-1,
                         tasks_limit=-1,
                         tasks_executions=-1)
