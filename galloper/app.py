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

from flask import Flask
from datetime import datetime

from flask_restful import Api

from galloper.config import Config
from galloper.database.db_manager import init_db, db_session
from galloper.api.routes import initialize_api_routes


def register_blueprints(flask_app: Flask) -> None:
    from galloper.routes import tasks, observer, artifacts, report, thresholds, projects
    flask_app.register_blueprint(projects.bp)
    flask_app.register_blueprint(tasks.bp)
    flask_app.register_blueprint(observer.bp)
    flask_app.register_blueprint(artifacts.bp)
    flask_app.register_blueprint(report.bp)
    flask_app.register_blueprint(thresholds.bp)


def register_api(flask_app: Flask) -> None:
    api = Api(flask_app, prefix="/api/v1", catch_all_404s=True)
    initialize_api_routes(api=api)


def create_app(config_class: type = Config) -> Flask:
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class())
    init_db()

    @flask_app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @flask_app.template_filter("ctime")
    def convert_time(ts):
        try:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "Not Executed"

    @flask_app.template_filter("is_zero")
    def return_zero(val):
        try:
            return round(val[0]/val[1], 2)
        except:
            return 0

    register_blueprints(flask_app=flask_app)
    register_api(flask_app=flask_app)
    return flask_app


app = create_app()


def main():
    config = Config()
    app.run(host=config.APP_HOST, port=config.APP_PORT, debug=True)


if __name__ == "__main__":
    main()
