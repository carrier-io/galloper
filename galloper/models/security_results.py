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

from galloper.models import db, BaseModel


class SecurityResults(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_time = db.Column(db.String(80), unique=False)
    scan_duration = db.Column(db.String(80), unique=False)
    project_name = db.Column(db.String(80), unique=False)
    app_name = db.Column(db.String(80), unique=False)
    endpoint = db.Column(db.String(80), unique=False)
    scan_type = db.Column(db.String(4), unique=False)
    findings = db.Column(db.Integer, unique=False)
    false_positives = db.Column(db.Integer, unique=False)
    excluded = db.Column(db.Integer, unique=False)
    info_findings = db.Column(db.Integer, unique=False)
    environment = db.Column(db.String(20), unique=False, nullable=False)





