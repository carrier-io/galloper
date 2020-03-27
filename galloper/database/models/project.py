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

from sqlalchemy import String, Column, Integer, JSON
from werkzeug.exceptions import NotFound

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base, db_session
from galloper.database.models.project_bucket import ProjectBucket
from galloper.utils.auth import SessionProject


class Project(AbstractBaseMixin, Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True)
    name = Column(String(256), unique=False)
    secrets_json = Column(JSON, unique=False)

    def used_in_session(self):
        selected_id = SessionProject.get()
        return self.id == selected_id

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        json_data = super().to_json(exclude_fields=exclude_fields)
        json_data["used_in_session"] = self.used_in_session()
        return json_data

    def get_buckets_names(self, internal: bool = False):
        return [
            getattr(project_bucket, "internal_bucket_name" if internal else "name")
            for project_bucket in
            ProjectBucket.query.filter(ProjectBucket.project_id == self.id).all()
        ]

    def get_bucket_internal_name(self, bucket_name: str) -> Optional[str]:
        try:
            instance = ProjectBucket.query.filter(
                ProjectBucket.project_id == self.id, ProjectBucket.name == bucket_name
            ).first_or_404()
        except NotFound:
            return None
        else:
            return instance.internal_bucket_name

    def create_bucket(self, bucket_name: str) -> ProjectBucket:
        project_bucket = ProjectBucket(project_id=self.id, name=bucket_name)
        project_bucket.insert()
        return project_bucket

    def delete_bucket(self, bucket_name: str, commit: bool = True) -> None:
        db_session.query(ProjectBucket).filter(
            ProjectBucket.project_id == self.id,
            ProjectBucket.name == bucket_name
        ).delete()
        if commit:
            db_session.commit()

    @classmethod
    def apply_full_delete_by_pk(cls, pk: int) -> None:
        import psycopg2

        from galloper.database.models.task_results import Results
        from galloper.database.models.task import Task
        from galloper.database.models.security_results import SecurityResults
        from galloper.database.models.security_reports import SecurityReport
        from galloper.database.models.security_details import SecurityDetails
        from galloper.database.models.api_reports import APIReport
        from galloper.database.models.api_release import APIRelease

        _logger = logging.getLogger(cls.__name__.lower())
        _logger.info("Start deleting entire project within transaction")

        # !TODO implement removal from minio
        # from galloper.processors.minio import MinioClient
        # project = cls.query.get_or_404(pk)
        # minio_client = MinioClient(project=project)
        # for bucket in minio_client.list_bucket():
        #     ...

        db_session.query(Project).filter_by(id=pk).delete()
        for model_class in (
            Results, Task, SecurityResults, SecurityReport, SecurityDetails, APIReport, APIRelease,
            ProjectBucket  # !TODO take a look on todo above
        ):
            db_session.query(model_class).filter_by(project_id=pk).delete()

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
            _logger.info("Project successfully deleted!")
