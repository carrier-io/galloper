#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from flask import Flask, g
from datetime import datetime

from galloper.models import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/db/test.db'
    app.config['UPLOAD_FOLDER'] = '/tmp/tasks'
    with app.app_context():
        db.init_app(app)

    @app.teardown_appcontext
    def teardown_db(event):
        db = g.pop('db', None)
        if db:
            db.close()

    @app.template_filter('ctime')
    def convert_time(ts):
        try:
            return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return "Not Executed"

    from galloper.routes import tasks, observer, artifacts
    app.register_blueprint(tasks.bp)
    app.register_blueprint(observer.bp)
    app.register_blueprint(artifacts.bp)

    with app.app_context():
        db.create_all(app=app)

    return app


def main():
    _app = create_app()
    host = "0.0.0.0"
    port = 5000
    _app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
