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

from functools import wraps

from flask import session, redirect, url_for

from galloper.config import Config


PROJECT_CACHE_KEY = Config().PROJECT_CACHE_KEY


def project_required(func):
    from galloper.database.models.project import Project

    @wraps(func)
    def decorated_function(*args, **kwargs):

        if PROJECT_CACHE_KEY not in session:
            return redirect(url_for("projects.add_project"))

        project_id = session[PROJECT_CACHE_KEY]
        project = Project.get_object_or_404(pk=project_id)
        return func(project, *args, **kwargs)
    return decorated_function


def set_project_to_session(project_id: int):
    session[PROJECT_CACHE_KEY] = project_id
