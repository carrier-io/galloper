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

import os
from typing import Optional

from galloper.utils.patterns import SingletonABC

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(metaclass=SingletonABC):
    APP_HOST: str = os.environ.get("IP") or "0.0.0.0"
    APP_PORT: int = int(os.environ.get("APP_PORT", 5000)) or 5000
    DATABASE_VENDOR: str = os.environ.get("DATABASE_VENDOR", "sqlite")
    DATABASE_URI: str = os.environ.get("DATABASE_URL") or "sqlite:////tmp/db/test.db"
    UPLOAD_FOLDER: str = os.environ.get("TASKS_UPLOAD_FOLDER", "/tmp/tasks")
    DATE_TIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    DATABASE_SCHEMA: Optional[str] = None

    SECRET_KEY = os.environ.get("SECRET_KEY", ":iMHK_F`4hyrE;Wfr;+Ui8l&R3wYiB")
    PROJECT_CACHE_KEY = os.environ.get("PROJECT_CACHE_KEY", "project_cache_key")

    def __init__(self) -> None:

        self.db_engine_config = {
            "isolation_level": "READ COMMITTED" if self.DATABASE_VENDOR != 'sqlite' else 'SERIALIZABLE',
            "echo": False
        }

        if self.DATABASE_VENDOR == "postgres":

            self.DATABASE_SCHEMA = os.environ.get("POSTGRES_SCHEMA", "carrier")

            host = os.environ.get("POSTGRES_HOST", "carrier-postgres")
            port = os.environ.get("POSTGRES_PORT", 5432)
            database = os.environ.get("POSTGRES_DB", "carrier")
            username = os.environ.get("POSTGRES_USER", "carrier")
            password = os.environ.get("POSTGRES_PASSWORD", "password")

            self.DATABASE_URI = "postgresql://{username}:{password}@{host}:{port}/{database}".format(
                username=username,
                password=password,
                host=host,
                port=port,
                database=database
            )

            self.db_engine_config["pool_size"] = 10
            self.db_engine_config["max_overflow"] = 5
