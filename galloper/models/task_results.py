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

from json import dumps
from galloper.models import db


class Results(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(80), unique=False, nullable=False)
    ts = db.Column(db.Integer, unique=False, nullable=False)
    results = db.Column(db.String(80), unique=False, nullable=False)
    log = db.Column(db.String(256), unique=False, nullable=False)

    def __repr__(self):
        return dumps(dict(task_id=self.task_id, ts=self.ts, results=self.results),indent=2)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def commit():
        db.session.commit()

