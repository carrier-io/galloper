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

import logging
from typing import Optional

from sqlalchemy import String, Column, Integer, JSON, Boolean

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base, db_session
from galloper.utils.auth import SessionProject


class Project(AbstractBaseMixin, Base):
    __tablename__ = "project"

    API_EXCLUDE_FIELDS = ("secrets_json", "worker_pool_config_json")

    id = Column(Integer, primary_key=True)
    name = Column(String(256), unique=False)
    project_owner = Column(String(256), unique=False)
    secrets_json = Column(JSON, unique=False, default={})
    worker_pool_config_json = Column(JSON, unique=False, default={})
    package = Column(String, nullable=False, default="basic")
    dast_enabled = Column(Boolean, nullable=False, default=False)
    sast_enabled = Column(Boolean, nullable=False, default=False)
    performance_enabled = Column(Boolean, nullable=False, default=False)

    def insert(self) -> None:
        from galloper.processors.minio import MinioClient
        super().insert()

        MinioClient(project=self).create_bucket(bucket="reports")

    def used_in_session(self):
        selected_id = SessionProject.get()
        return self.id == selected_id

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        json_data = super().to_json(exclude_fields=exclude_fields)
        json_data["used_in_session"] = self.used_in_session()
        return json_data

    def get_data_retention_limit(self) -> Optional[int]:
        from galloper.database.models.project_quota import ProjectQuota
        project_quota = ProjectQuota.query.filter_by(project_id=self.id).first()
        if project_quota and project_quota.data_retention_limit:
            return project_quota.data_retention_limit

    @classmethod
    def apply_full_delete_by_pk(cls, pk: int) -> None:
        import docker
        import psycopg2

        from galloper.processors.minio import MinioClient
        from galloper.dal.influx_results import delete_test_data

        from galloper.database.models.task_results import Results
        from galloper.database.models.task import Task
        from galloper.database.models.security_results import SecurityResults
        from galloper.database.models.security_reports import SecurityReport
        from galloper.database.models.security_details import SecurityDetails
        from galloper.database.models.api_reports import APIReport
        from galloper.database.models.api_release import APIRelease

        _logger = logging.getLogger(cls.__name__.lower())
        _logger.info("Start deleting entire project within transaction")

        project = cls.query.get_or_404(pk)
        minio_client = MinioClient(project=project)
        docker_client = docker.from_env()
        buckets_for_removal = minio_client.list_bucket()

        db_session.query(Project).filter_by(id=pk).delete()
        for model_class in (
            Results, SecurityResults, SecurityReport, SecurityDetails, APIRelease
        ):
            db_session.query(model_class).filter_by(project_id=pk).delete()

        
        influx_result_data = []
        for api_report in APIReport.query.filter_by(project_id=pk).all():
            influx_result_data.append(
                (api_report.build_id, api_report.name, api_report.lg_type)
            )
            api_report.delete(commit=False)

        task_ids = []
        for task in Task.query.filter_by(project_id=pk).all():
            task_ids.append(task.task_id)
            task.delete(commit=False)

        try:
            db_session.flush()
        except (psycopg2.DatabaseError,
                psycopg2.DataError,
                psycopg2.ProgrammingError,
                psycopg2.OperationalError,
                psycopg2.IntegrityError,
                psycopg2.InterfaceError,
                psycopg2.InternalError,
                psycopg2.Error) as exc:
            db_session.rollback()
            _logger.error(str(exc))
        else:
            db_session.commit()
            for bucket in buckets_for_removal:
                minio_client.remove_bucket(bucket=bucket)
            for influx_item_data in influx_result_data:
                delete_test_data(*influx_item_data)
            for task_id in task_ids:
                try:
                    volume = docker_client.volumes.get(task_id)
                except docker.errors.NotFound as docker_exc:
                    _logger.info(str(docker_exc))
                else:
                    volume.remove(force=True)
            _logger.info("Project successfully deleted!")

        selected_project_id = SessionProject.get()
        if pk == selected_project_id:
            SessionProject.pop()
