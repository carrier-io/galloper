import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    APP_HOST: str = os.environ.get("APP_HOST") or "0.0.0.0"
    APP_PORT: int = int(os.environ.get("APP_PORT", 5000)) or 5000
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL") or "sqlite:////tmp/db/test.db"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    UPLOAD_FOLDER: str = "/tmp/tasks"
    DATE_TIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        host = os.environ.get("POSTGRES_HOST")
        port = os.environ.get("POSTGRES_PORT", 5432)
        database = os.environ.get("POSTGRES_DB")
        username = os.environ.get("POSTGRES_USER")
        password = os.environ.get("POSTGRES_PASSWORD")
        schema = os.environ.get("POSTGRES_SCHEMA")

        if all((host, database, username, password)):
            self.SQLALCHEMY_DATABASE_URI = "postgresql://{username}:{password}@{host}:{port}/{database}".format(
                username=username,
                password=password,
                host=host,
                port=port,
                database=database
            )
            self.POSTGRES_SCHEMA = schema
