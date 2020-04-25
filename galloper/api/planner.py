from uuid import uuid4
from flask_restful import Resource
from json import loads
from werkzeug.datastructures import FileStorage
from flask import request, current_app
from sqlalchemy import and_, or_
from galloper.api.base import get, upload_file, run_task
from galloper.database.models.project import Project
from galloper.database.models.performance_tests import PerformanceTests
from galloper.utils.api_utils import build_req_parser


class TestsApiPerformance(Resource):
    _get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args")
    )

    _post_rules = (
        dict(name="file", type=FileStorage, location='files'),
        dict(name="name", type=str, location='form'),
        dict(name="entrypoint", type=str, location='form'),
        dict(name="parallel", type=int, location='form'),
        dict(name="reporter", type=str, location='form'),
        dict(name="runner", type=str, location='form'),
        dict(name="params", type=str, location='form'),
        dict(name="env_vars", type=str, location='form'),
        dict(name="customization", type=str, location='form'),
        dict(name="java_opts", type=str, location='form')
    )

    _delete_rules = (
        dict(name="id[]", type=int, action="append", location="args"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)
        self.post_parser = build_req_parser(rules=self._post_rules)
        self.delete_parser = build_req_parser(rules=self._delete_rules)

    def get(self, project_id: int):
        args = self.get_parser.parse_args(strict=False)
        reports = []
        total, res = get(project_id, args, PerformanceTests)
        for each in res:
            reports.append(each.to_json())
        return {"total": total, "rows": reports}

    def post(self, project_id: int):
        current_app.logger.info(request.form)
        args = self.post_parser.parse_args(strict=False)
        project = Project.query.get_or_404(project_id)
        file_name = args["file"].filename
        bucket = "tests"
        upload_file(bucket, args["file"], project, create_if_not_exists=True)
        test = PerformanceTests(project_id=project.id,
                                test_uid=str(uuid4()),
                                name=args["name"],
                                parallel=args["parallel"],
                                bucket=bucket,
                                file=file_name,
                                entrypoint=args["entrypoint"],
                                runner=args["runner"],
                                reporting=args["reporter"].split(","),
                                params=loads(args["params"]),
                                env_vars=loads(args["env_vars"]),
                                customization=loads(args["customization"]),
                                java_opts=args["java_opts"])
        test.insert()
        current_app.logger.info(test.to_json())
        return test.to_json(exclude_fields=("id",))

    def delete(self, project_id: int):
        args = self.delete_parser.parse_args(strict=False)
        project = Project.query.get_or_404(project_id)
        query_result = PerformanceTests.query.filter(
            and_(PerformanceTests.project_id == project.id, PerformanceTests.id.in_(args["id[]"]))
        ).all()
        for each in query_result:
            each.delete()
        return {"message": "deleted"}


class TestApiBackend(Resource):
    _post_rules = (
        dict(name="test_type", type=str, required=False, location='json'),
        dict(name="parallel", type=int, required=False, location='json'),
        dict(name="reporter", type=str, required=False, location='json'),
        dict(name="runner", type=list, required=False, location='json'),
        dict(name="params", type=list, required=False, location='json'),
        dict(name="env_vars", type=list, required=False, location='json'),
        dict(name="customization", type=list, required=False, location='json'),
        dict(name="java_opts", type=str, required=False, location='json')
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.post_parser = build_req_parser(rules=self._post_rules)

    def get(self, project_id, test_id):
        project = Project.query.get_or_404(project_id)
        if isinstance(test_id, int):
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.id == test_id)
        else:
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.test_uid == test_id)
        test = PerformanceTests.query.filter(_filter).first()
        return test.configure_execution_json()

    def post(self, project_id, test_id):
        project = Project.query.get_or_404(project_id)
        args = self.post_parser.parse_args(strict=False)
        if isinstance(test_id, int):
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.id == test_id)
        else:
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.test_uid == test_id)
        task = PerformanceTests.query.filter(_filter).first()
        event = list()
        event.append(task.configure_execution_json(test_type=args.get("test_type"),
                                                   params=args.get("params", None),
                                                   env_vars=args.get("env_vars", None),
                                                   reporting=args.get("reporting", None),
                                                   customization=args.get("customization", None),
                                                   java_opts=args.get("java_opts", None),
                                                   parallel=args.get("parallel", None)))
        response = run_task(project.secrets_json["cc"], event)
        response["redirect"] = f'{project.secrets_json["cc"]}/results'
        return response
