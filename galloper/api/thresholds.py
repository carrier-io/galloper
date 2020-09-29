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

from flask_restful import Resource
from sqlalchemy import and_

from galloper.dal.influx_results import get_threholds, create_thresholds, delete_threshold
from galloper.database.models.api_reports import APIReport
from galloper.database.models.ui_report import UIReport
from galloper.database.models.ui_result import UIResult
from galloper.database.models.ui_thresholds import UIThresholds
from galloper.database.models.project import Project
from galloper.database.models.security_thresholds import SecurityThresholds
from galloper.database.models.security_tests import SecurityTestsSAST, SecurityTestsDAST
from galloper.utils.api_utils import build_req_parser


class BackendThresholdsAPI(Resource):
    get_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="environment", type=str, location="args")
    )
    delete_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="test", type=str, location=("args", "json")),
        dict(name="scope", type=str, location=("args", "json")),
        dict(name="target", type=str, location=("args", "json")),
        dict(name="aggregation", type=str, location=("args", "json")),
        dict(name="comparison", type=str, location=("args", "json")),
        dict(name="env", type=str, location=("args", "json"))
    )
    post_rules = delete_rules + (
        dict(name="yellow", type=float, location="json"),
        dict(name="red", type=float, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def get(self):
        args = self._parser_get.parse_args(strict=False)
        return get_threholds(test_name=args.get("name"), environment=args.get("environment"))

    def post(self):
        args = self._parser_post.parse_args(strict=False)
        return {"message": create_thresholds(
            test=args["test"],
            scope=args["scope"],
            target=args["target"],
            aggregation=args["aggregation"],
            comparison=args["comparison"],
            yellow=args["yellow"],
            red=args["red"],
            environment=args["env"]
        )}

    def delete(self):
        args = self._parser_delete.parse_args(strict=False)
        delete_threshold(
            test=args["test"],
            environment=args["env"],
            target=args["target"],
            scope=args["scope"],
            aggregation=args["aggregation"],
            comparison=args["comparison"]
        )
        return {"message": "OK"}


class UIThresholdsAPI(Resource):
    get_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="environment", type=str, location="args")
    )
    delete_rules = (
        dict(name="test", type=str, location=("args", "json")),
        dict(name="scope", type=str, location=("args", "json")),
        dict(name="target", type=str, location=("args", "json")),
        dict(name="aggregation", type=str, location=("args", "json")),
        dict(name="comparison", type=str, location=("args", "json")),
        dict(name="env", type=str, location=("args", "json"))
    )

    post_rules = delete_rules + (
        dict(name="metric", type=str, location=("args", "json")),
        dict(name="name", type=str, location=("args", "json")),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def get(self, project_id: int):
        project = Project.get_or_404(project_id)
        args = self._parser_get.parse_args(strict=False)
        res = UIThresholds.query.filter().filter(
            and_(UIThresholds.project_id == project.id,
                 UIThresholds.test == args.get("name"),
                 UIThresholds.environment == args.get("environment"))).all()
        return [th.to_json() for th in res]

    def post(self, project_id: int):
        project = Project.get_or_404(project_id)
        args = self._parser_post.parse_args(strict=False)
        UIThresholds(project_id=project.id,
                     name=args['name'],
                     test=args["test"],
                     scope=args["scope"],
                     environment=args["env"],
                     metric=args["metric"],
                     target=args["target"],
                     aggregation=args["aggregation"],
                     comparison=args["comparison"]).insert()
        return {"message": "OK"}

    def delete(self, project_id: int):
        project = Project.get_or_404(project_id)
        args = self._parser_delete.parse_args(strict=False)
        UIThresholds.query.filter().filter(
            and_(UIThresholds.project_id == project.id,
                 UIThresholds.test == args.get("test"),
                 UIThresholds.scope == args.get("scope"),
                 UIThresholds.environment == args.get("env"),
                 UIThresholds.aggregation == args.get("aggregation"),
                 UIThresholds.comparison == args.get("comparison"))).first().delete()
        return {"message": "OK"}


class RequestsAPI(Resource):
    get_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="type", type=str, default="backend", location="args")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    @staticmethod
    def _get_backend_requests(project_id, name):
        requests_data = set()
        query_result = APIReport.query.filter(
            and_(APIReport.name == name, APIReport.project_id == project_id)
        ).order_by(APIReport.id.asc()).all()
        for each in query_result:
            requests_data.update(set(each.requests.split(";")))
        return list(requests_data)

    @staticmethod
    def _get_ui_pages(project_id, name):
        page_names = {}
        reports = UIReport.query.filter(and_(UIReport.project_id == project_id, UIReport.name == name)).all()
        report_ids = [report.uid for report in reports]
        results = UIResult.query.filter(UIResult.report_uid.in_(report_ids)).all()
        for each in results:
            page_names[each.name] = each.identifier
        return page_names

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        if args.get("type") == "ui":
            return self._get_ui_pages(project.id, args.get("name"))
        else:
            return self._get_backend_requests(project.id, args.get("name"))


class EnvironmentsAPI(Resource):
    get_rules = (
        dict(name="name", type=str, location="args"),
        dict(name="type", type=str, default="backend", location="args")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        model = APIReport
        if args.get("type") == "ui":
            model = UIReport
        query_result = model.query.with_entities(model.environment).distinct().filter(
            and_(model.name == args.get("name"),
                 model.project_id == project.id)
        ).order_by(model.id.asc()).all()
        return list(set([each.environment for each in query_result]))


class SecurityThresholdsAPI(Resource):
    get_rules = (
        dict(name="test_uid", type=str, location="args"),
    )

    post_rules = (
        dict(name="test_uid", type=str, location=("json")),
        dict(name="critical", type=int, location=("json")),
        dict(name="high", type=int, location=("json")),
        dict(name="medium", type=int, location=("json")),
        dict(name="low", type=int, location=("json")),
        dict(name="info", type=int, location=("json"))
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        threshold = SecurityThresholds.query.filter(and_(SecurityThresholds.test_uid == args['test_uid'],
                                                         SecurityThresholds.project_id == project.id)).first()
        return threshold.to_json(exclude_fields=("id"))

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        threshold = SecurityThresholds.query.filter(and_(SecurityThresholds.test_uid == args['test_uid'],
                                                         SecurityThresholds.project_id == project.id)).first()

        if not threshold:
            test_name = SecurityTestsSAST.query.filter(and_(SecurityTestsSAST.test_uid == args['test_uid'],
                                                            SecurityTestsSAST.project_id == project.id)).first()
            if test_name:
                name = test_name.name
            else:
                test_name = SecurityTestsDAST.query.filter(and_(SecurityTestsDAST.test_uid == args['test_uid'],
                                                                SecurityTestsDAST.project_id == project.id)).first()
                name = test_name.name
            threshold = SecurityThresholds(project_id=project.id, test_name=name,
                                           test_uid=args["test_uid"], critical=-1,
                                           high=-1, medium=-1, low=-1, info=-1,
                                           critical_life=-1, high_life=-1, medium_life=-1,
                                           low_life=-1, info_life=-1)
            op = threshold.insert
        else:
            op = threshold.commit
        threshold.critical = args['critical']
        threshold.high = args['high']
        threshold.medium = args['medium']
        threshold.low = args['low']
        threshold.info = args['info']
        op()
        return threshold.to_json(exclude_fields=("id"))


