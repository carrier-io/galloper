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

from galloper.config import Config
from galloper.database.db_manager import init_db, db_session


def register_blueprints(app: Flask) -> None:
    from galloper.routes import tasks, observer, artifacts, report, thresholds, api_release
    app.register_blueprint(tasks.bp)
    app.register_blueprint(observer.bp)
    app.register_blueprint(artifacts.bp)
    app.register_blueprint(report.bp)
    app.register_blueprint(thresholds.bp)
    app.register_blueprint(api_release.bp)


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class())
    init_db()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @app.template_filter('ctime')
    def convert_time(ts):
        try:
            return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return "Not Executed"

    @app.template_filter('is_zero')
    def return_zero(val):
        try:
            return round(val[0]/val[1], 2)
        except:
            return 0

    register_blueprints(app)

    return app


def main() -> None:
    _app = create_app()
    config = Config()
    _app.run(host=config.APP_HOST, port=config.APP_PORT, debug=True)


if __name__ == "__main__":
    main()
