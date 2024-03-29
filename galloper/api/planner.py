from copy import deepcopy
from uuid import uuid4
from flask_restful import Resource
from json import loads
from werkzeug.datastructures import FileStorage
from flask import request, current_app
from sqlalchemy import and_
from galloper.api.base import get, upload_file, run_task, compile_tests
from galloper.database.models.project import Project
from galloper.database.models.performance_tests import PerformanceTests, UIPerformanceTests
from galloper.database.models.security_tests import SecurityTestsDAST, SecurityTestsSAST
from galloper.utils.api_utils import build_req_parser, str2bool


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
        dict(name="git", type=str, location='form'),
        dict(name="name", type=str, location='form'),
        dict(name="entrypoint", type=str, location='form'),
        dict(name="parallel", type=int, location='form'),
        dict(name="region", type=str, location='form'),
        dict(name="reporter", type=str, location='form'),
        dict(name="emails", type=str, location='form'),
        dict(name="runner", type=str, location='form'),
        dict(name="compile", type=str2bool, location='form'),
        dict(name="params", type=str, location='form'),
        dict(name="env_vars", type=str, location='form'),
        dict(name="customization", type=str, location='form'),
        dict(name="cc_env_vars", type=str, location='form')
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
        project = Project.get_or_404(project_id)
        if args.get("git"):
            file_name = ""
            bucket = ""
            git_settings = loads(args["git"])
        else:
            git_settings = {}
            file_name = args["file"].filename
            bucket = "tests"
            upload_file(bucket, args["file"], project, create_if_not_exists=True)

        if args["compile"] and args["runner"] in ["v3.1", "v2.3"]:
            compile_tests(project.id, file_name, args["runner"])

        reporting = args["reporter"].split(",") if args["reporter"] else []
        test = PerformanceTests(project_id=project.id,
                                test_uid=str(uuid4()),
                                name=args["name"],
                                parallel=args["parallel"],
                                region=args["region"],
                                bucket=bucket,
                                file=file_name,
                                git=git_settings,
                                entrypoint=args["entrypoint"],
                                runner=args["runner"],
                                reporting=reporting,
                                emails=args["emails"],
                                params=loads(args["params"]),
                                env_vars=loads(args["env_vars"]),
                                customization=loads(args["customization"]),
                                cc_env_vars=loads(args["cc_env_vars"]))
        test.insert()
        current_app.logger.info(test.to_json())
        return test.to_json(exclude_fields=("id",))

    def delete(self, project_id: int):
        args = self.delete_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        query_result = PerformanceTests.query.filter(
            and_(PerformanceTests.project_id == project.id, PerformanceTests.id.in_(args["id[]"]))
        ).all()
        for each in query_result:
            each.delete()
        return {"message": "deleted"}


class TestApi(Resource):

    def get(self, project_id, test_uuid):
        project = Project.get_or_404(project_id)
        job_type = "not_found"
        # check if APIPerformanceTests
        _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.test_uid == test_uuid)
        test = PerformanceTests.query.filter(_filter).first()
        if test:
            job_type = test.job_type

        _filter = and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.test_uid == test_uuid)
        test = UIPerformanceTests.query.filter(_filter).first()
        if test:
            job_type = test.job_type

        _filter = and_(
            SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.test_uid == test_uuid
        )
        test = SecurityTestsDAST.query.filter(_filter).first()
        if test:
            job_type = "dast"

        _filter = and_(
            SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.test_uid == test_uuid
        )
        test = SecurityTestsSAST.query.filter(_filter).first()
        if test:
            job_type = "sast"

        return {"job_type": job_type}


class TestApiBackend(Resource):
    _get_rules = (
        dict(name="raw", type=int, default=0, location="args"),
        dict(name="type", type=str, default='cc', location="args"),
        dict(name="exec", type=str2bool, default=False, location="args"),
        dict(name="source", type=str, default='legacy', location="args")
    )

    _put_rules = (
        dict(name="parallel", type=int, required=False, location='json'),
        dict(name="region", type=str, required=False, location='json'),
        dict(name="params", type=str, default="{}", required=False, location='json'),
        dict(name="env_vars", type=str, default="{}", required=False, location='json'),
        dict(name="customization", type=str, default="{}", required=False, location='json'),
        dict(name="cc_env_vars", type=str, default="{}", required=False, location='json'),
        dict(name="reporter", type=list, required=False, location='json'),
        dict(name="emails", type=str, required=False, location='json'),
        dict(name="git", type=str, required=False, location='json'),
    )

    _post_rules = _put_rules + (
        dict(name="test_type", type=str, required=False, location='json'),
        dict(name="runner", type=str, required=False, location='json'),
        dict(name="type", type=str, default=None, required=False, location='json')
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)
        self.put_parser = build_req_parser(rules=self._put_rules)
        self.post_parser = build_req_parser(rules=self._post_rules)

    def get(self, project_id, test_id):
        args = self.get_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        if isinstance(test_id, int):
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.id == test_id)
        else:
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.test_uid == test_id)
        test = PerformanceTests.query.filter(_filter).first()
        if test.git and type(test.git) is dict and test.git['repo_pass'] is not None and len(test.git['repo_pass']) and args["source"] == "galloper":
            if not test.git['repo_pass'].startswith("{{") and not test.git['repo_pass'].endswith("}}"):
                test.git['repo_pass'] = "********"
        if args.raw:
            return test.to_json(["influx.port", "influx.host", "galloper_url",
                                 "influx.db", "comparison_db", "telegraf_db",
                                 "loki_host", "loki_port", "influx.username", "influx.password"])
        if args["type"] == "docker":
            message = test.configure_execution_json(args.get("type"), execution=args.get("exec"))
        else:
            message = [{"test_id": test.test_uid}]
        return {"config": message}  # this is cc format

    def put(self, project_id, test_id):
        default_params = ["influx.port", "influx.host", "galloper_url", "influx.db", "comparison_db", "telegraf_db",
                          "loki_host", "loki_port", "test.type", "test_type", "influx.username", "influx.password"]
        project = Project.get_or_404(project_id)
        args = self.put_parser.parse_args(strict=False)
        if isinstance(test_id, int):
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.id == test_id)
        else:
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.test_uid == test_id)
        task = PerformanceTests.query.filter(_filter).first()

        for each in ["params", "env_vars", "customization", "cc_env_vars"]:
            params = deepcopy(getattr(task, each))
            for key in list(params.keys()):
                if key not in loads(args.get(each)).keys() and key not in default_params:
                    del params[key]
            for key, value in loads(args.get(each)).items():
                if key not in params or params[key] != value:
                    params[key] = value
            setattr(task, each, params)

        if args.get("reporter"):
            task.reporting = args["reporter"]
        else:
            task.reporting = []

        if args.get("emails"):
            task.emails = args["emails"]
        else:
            task.emails = ""

        if args.get("parallel"):
            task.parallel = args.get("parallel")
        if args.get("region"):
            task.region = args.get("region")
        if args.get("git"):
            args_git = loads(args.get("git"))
            # ignore password change from UI
            if "repo_pass" in task.git:
                args_git["repo_pass"] = task.git["repo_pass"]
            task.git = args_git
        task.commit()
        return task.to_json(["influx.port", "influx.host", "galloper_url",
                             "influx.db", "comparison_db", "telegraf_db",
                             "loki_host", "loki_port", "influx.username", "influx.password"])

    def post(self, project_id, test_id):
        project = Project.get_or_404(project_id)
        args = self.post_parser.parse_args(strict=False)
        if isinstance(test_id, int):
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.id == test_id)
        else:
            _filter = and_(PerformanceTests.project_id == project.id, PerformanceTests.test_uid == test_id)
        task = PerformanceTests.query.filter(_filter).first()
        event = list()
        execution = True if args['type'] and args["type"] == "config" else False
        event.append(task.configure_execution_json(output='cc',
                                                   test_type=args.get("test_type"),
                                                   params=loads(args.get("params", None)),
                                                   env_vars=loads(args.get("env_vars", None)),
                                                   reporting=args.get("reporter", None),
                                                   customization=loads(args.get("customization", None)),
                                                   cc_env_vars=loads(args.get("cc_env_vars", None)),
                                                   parallel=args.get("parallel", None),
                                                   region=args.get("region", "default"),
                                                   execution=execution, emails=args.get("emails", None)))
        if args['type'] and args["type"] == "config":
            return event[0]
        for each in event:
            each["test_id"] = task.test_uid
        response = run_task(project.id, event)
        response["redirect"] = f'/task/{response["task_id"]}/results'
        return response
