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

from sqlalchemy import String, Column, Integer, Text

from galloper.database.db_manager import Base
from galloper.database.abstract_base import AbstractBaseMixin


class SecurityDetails(AbstractBaseMixin, Base):
    __tablename__ = "security_details"

    id = Column(Integer, primary_key=True)
    detail_hash = Column(String(80), unique=False)
    details = Column(Text, unique=False)
