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
from typing import Optional

from sqlalchemy import String, Column, Integer, JSON
from werkzeug.exceptions import NotFound

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base
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

    def get_buckets_names(self):
        return [
            project_bucket.name for project_bucket in
            ProjectBucket.query.filter(ProjectBucket.project_id == self.id).all()
        ]

    def get_bucket_internal_name(self, bucket_name: str) -> Optional[str]:
        try:
            instance = ProjectBucket.get_object_or_404(
                custom_params=(ProjectBucket.project_id == self.id, ProjectBucket.name == bucket_name)
            )
        except NotFound:
            return None
        else:
            return instance.internal_bucket_name

    def create_bucket(self, bucket_name: str) -> ProjectBucket:
        project_bucket = ProjectBucket(project_id=self.id, name=bucket_name)
        project_bucket.insert()
        return project_bucket

    def delete_bucket(self, bucket_name: str) -> None:
        ProjectBucket.get_and_delete_object(
            custom_params=(ProjectBucket.project_id == self.id, ProjectBucket.name == bucket_name)
        )
