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


class SecurityReport(AbstractBaseMixin, Base):
    __tablename__ = "security_report"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    report_id = Column(Integer, nullable=False)
    issue_hash = Column(String(128), unique=False)
    tool_name = Column(String(128), unique=False)
    description = Column(String(128), unique=False)
    severity = Column(String(16), unique=False)
    details = Column(Integer, unique=False)
    endpoints = Column(Text, unique=False)
    false_positive = Column(Integer, unique=False)
    info_finding = Column(Integer, unique=False)
    excluded_finding = Column(Integer, unique=False)
