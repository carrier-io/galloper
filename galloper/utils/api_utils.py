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

from flask_restful import Api, Resource, reqparse


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    return False


def build_req_parser(rules: tuple, location=("json", "values")) -> reqparse.RequestParser:
    request_parser = reqparse.RequestParser()
    for rule in rules:
        if isinstance(rule, dict):
            kwargs = rule.copy()
            name = kwargs["name"]
            del kwargs["name"]
            if "location" not in kwargs:
                # Use global location unless it"s specified by the rule.
                kwargs["location"] = location
            request_parser.add_argument(name, **kwargs)

        elif isinstance(rule, (list, tuple)):
            name, _type, required, default = rule
            kwargs = {
                "type": _type,
                "location": location,
                "required": required
            }
            if default is not None:
                kwargs["default"] = default
            request_parser.add_argument(name, **kwargs)

    return request_parser


def add_resource_to_api(api: Api, resource: Resource, *urls, **kwargs) -> None:
    # This /api/v1 thing is made here to be able to register auth endpoints for local development
    urls = (*(f"/api/v1{url}" for url in urls), *(f"/api/v1{url}/" for url in urls))
    api.add_resource(resource, *urls, **kwargs)
