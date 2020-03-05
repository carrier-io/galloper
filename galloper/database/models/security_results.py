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

from sqlalchemy import String, Column, Integer

from galloper.database.db_manager import Base
from galloper.database.abstract_base import AbstractBaseMixin


class SecurityResults(AbstractBaseMixin, Base):
    __tablename__ = "security_results"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    scan_time = Column(String(128), unique=False)
    scan_duration = Column(String(128), unique=False)
    project_name = Column(String(128), unique=False)
    app_name = Column(String(128), unique=False)
    dast_target = Column(String(128), unique=False)
    sast_code = Column(String(128), unique=False)
    scan_type = Column(String(4), unique=False)
    findings = Column(Integer, unique=False)
    false_positives = Column(Integer, unique=False)
    excluded = Column(Integer, unique=False)
    info_findings = Column(Integer, unique=False)
    environment = Column(String(32), unique=False, nullable=False)
