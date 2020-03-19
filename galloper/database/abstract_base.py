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

import json
from typing import Any, Optional

from werkzeug.exceptions import NotFound

from galloper.config import Config
from galloper.database.db_manager import db_session

config = Config()


class AbstractBaseMixin:
    __table__ = None
    __table_args__ = {"schema": config.DATABASE_SCHEMA} if config.DATABASE_SCHEMA else None

    def __repr__(self) -> str:
        return json.dumps(self.to_json(), indent=2)

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns if column not in exclude_fields
        }

    @staticmethod
    def commit() -> None:
        db_session.commit()

    def add(self) -> None:
        db_session.add(self)

    def insert(self) -> None:
        db_session.add(self)
        self.commit()

    def delete(self) -> None:
        db_session.delete(self)
        self.commit()

    @classmethod
    def get_object_or_404(
        cls, pk: int, pk_field_name: str = "id", custom_params: Optional[Any] = None
    ) -> object:
        if not custom_params:
            instance = cls.query.filter_by(**{pk_field_name: pk}).first()
        else:
            instance = cls.query.filter(custom_params).first()
        if not instance:
            raise NotFound(description=f"{cls.__name__} object not found")
        return instance
