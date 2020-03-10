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
from typing import Optional

from flask_restful import Resource

from galloper.database.models.project import Project


class ProjectAPI(Resource):

    def get(self, project_id: Optional[int] = None):
        if project_id:
            project = Project.get_object_or_404(pk=project_id)
            return project.to_json()

        return [each.to_json() for each in Project.query.all()]
