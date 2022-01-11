import json
from copy import deepcopy
from json import loads
from uuid import uuid4

from flask import current_app
from flask_restful import Resource
from sqlalchemy import and_
from werkzeug.datastructures import FileStorage

from galloper.api.base import upload_file, get, run_task
from galloper.database.models.performance_tests import UIPerformanceTests
from galloper.database.models.project import Project
from galloper.database.models.statistic import Statistic
from galloper.utils.api_utils import build_req_parser, str2bool
from galloper.constants import CURRENT_RELEASE


class UITestsApiPerformance(Resource):
    _get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args"),
        dict(name="type", type=str, location="args")
    )

    _post_rules = (
        dict(name="file", type=FileStorage, location='files'),
        dict(name="git", type=str, location='form'),
        dict(name="name", type=str, location='form'),
        dict(name="entrypoint", type=str, location='form'),
        dict(name="reporter", type=str, location='form'),
        dict(name="browser", type=str, location='form'),
        dict(name="params", type=str, location='form'),
        dict(name="env_vars", type=str, location='form'),
        dict(name="loops", type=int, location='form', default=1),
        dict(name="region", type=str, location='form', default="default"),
        dict(name="runner", type=str, location='form', default="Observer"),
        dict(name="aggregation", type=str, location='form', default="max"),
        dict(name="customization", type=str, location='form'),
        dict(name="cc_env_vars", type=str, location='form'),
        dict(name="emails", type=str, location='form'),
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
        total, res = get(project_id, args, UIPerformanceTests)
        for each in res:
            reports.append(each.to_json())
        return {"total": total, "rows": reports}

    def post(self, project_id: int):
        args = self.post_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)

        browser = args["browser"] if args["browser"] != "Nothing selected" else "Chrome_undefined"
        runner = f"getcarrier/observer:{CURRENT_RELEASE}" if args["runner"] == "Observer" else \
                 f"getcarrier/observer-lighthouse:{CURRENT_RELEASE}"
        job_type = "observer"

        if args.get("git"):
            file_name = ""
            bucket = ""
            git_settings = loads(args["git"])
        else:
            git_settings = {}
            file_name = args["file"].filename
            bucket = "tests"
            upload_file(bucket, args["file"], project, create_if_not_exists=True)

        env_vars = loads(args["env_vars"])
        if "ENV" not in env_vars.keys():
            env_vars['ENV'] = 'Default'
        if args.get("region") == "":
            args["region"] = "default"

        test = UIPerformanceTests(project_id=project.id,
                                  test_uid=str(uuid4()),
                                  name=args["name"],
                                  bucket=bucket,
                                  file=file_name,
                                  entrypoint=args["entrypoint"],
                                  runner=runner,
                                  emails=args['emails'],
                                  browser=browser,
                                  git=git_settings,
                                  parallel=1,
                                  reporting=args["reporter"].split(","),
                                  params=loads(args["params"]),
                                  env_vars=env_vars,
                                  customization=loads(args["customization"]),
                                  cc_env_vars=loads(args["cc_env_vars"]),
                                  job_type=job_type,
                                  loops=args['loops'],
                                  region=args['region'],
                                  aggregation=args['aggregation'])
        test.insert()
        current_app.logger.info(test.to_json())
        return test.to_json(exclude_fields=("id",))

    def delete(self, project_id: int):
        args = self.delete_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        query_result = UIPerformanceTests.query.filter(
            and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.id.in_(args["id[]"]))
        ).all()
        for each in query_result:
            each.delete()
        return {"message": "deleted"}


class TestApiFrontend(Resource):
    _get_rules = (
        dict(name="raw", type=int, default=0, location="args"),
        dict(name="type", type=str, default='cc', location="args"),
        dict(name="exec", type=str2bool, default=False, location="args")
    )

    _put_rules = (
        dict(name="params", type=str, default="{}", required=False, location='json'),
        dict(name="env_vars", type=str, default="{}", required=False, location='json'),
        dict(name="customization", type=str, default="{}", required=False, location='json'),
        dict(name="cc_env_vars", type=str, default="{}", required=False, location='json'),
        dict(name="reporter", type=list, required=False, location='json'),
        dict(name="loops", type=int, required=False, location='json'),
        dict(name="region", type=str, required=False, location='json'),
        dict(name="aggregation", type=str, required=False, location='json'),
        dict(name="browser", type=str, required=False, location='json'),
        dict(name="entrypoint", type=str, required=False, location='json'),
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
            _filter = and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.id == test_id)
        else:
            _filter = and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.test_uid == test_id)
        test = UIPerformanceTests.query.filter(_filter).first()
        if args.raw:
            return test.to_json(["galloper_url"])
        if args["type"] == "docker":
            message = test.configure_execution_json(args.get("type"), execution=args.get("exec"))
        else:
            message = [{"test_id": test.test_uid}]
        return {"config": message}  # this is cc format

    def put(self, project_id, test_id):
        default_params = ["influx.port", "influx.host", "galloper_url", "influx.db", "test_name", "comparison_db",
                          "loki_host", "loki_port", "test.type", "test_type"]
        project = Project.get_or_404(project_id)
        args = self.put_parser.parse_args(strict=False)
        if isinstance(test_id, int):
            _filter = and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.id == test_id)
        else:
            _filter = and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.test_uid == test_id)
        task = UIPerformanceTests.query.filter(_filter).first()

        for each in ["params", "env_vars", "customization", "cc_env_vars"]:
            params = deepcopy(getattr(task, each))
            for key in list(params.keys()):
                if key not in loads(args.get(each)).keys() and key not in default_params:
                    del params[key]
            for key, value in loads(args.get(each)).items():
                if key not in params or params[key] != value:
                    params[key] = value
            setattr(task, each, params)

        task.reporting = args["reporter"]
        task.loops = args['loops']
        if args.get("region"):
            task.region = args.get("region")
        task.aggregation = args['aggregation']
        browser = args["browser"] if args["browser"] != "Nothing selected" else "Chrome_undefined"
        task.browser = browser
        task.entrypoint = args['entrypoint']
        task.emails = args['emails']
        task.git = json.loads(args['git'])
        task.commit()
        return task.to_json()

    def post(self, project_id, test_id):
        project = Project.get_or_404(project_id)
        args = self.post_parser.parse_args(strict=False)
        if isinstance(test_id, int):
            _filter = and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.id == test_id)
        else:
            _filter = and_(UIPerformanceTests.project_id == project.id, UIPerformanceTests.test_uid == test_id)
        task = UIPerformanceTests.query.filter(_filter).first()
        event = list()
        execution = True if args['type'] and args["type"] == "config" else False

        for browser in list(map(lambda x: x.strip(), task.browser.split(","))):
            event.append(task.configure_execution_json(output='cc',
                                                       browser=browser,
                                                       test_type=args.get("test_type"),
                                                       params=loads(args.get("params", None)),
                                                       env_vars=loads(args.get("env_vars", None)),
                                                       reporting=args.get("reporter", None),
                                                       customization=loads(args.get("customization", None)),
                                                       cc_env_vars=loads(args.get("cc_env_vars", None)),
                                                       parallel=args.get("parallel", None),
                                                       execution=execution))

        current_app.logger.error(f"Observer event sent {event}")
        if args['type'] and args["type"] == "config":
            return event[0]
        response = run_task(project.id, event)
        response["redirect"] = f'/task/{response["task_id"]}/results'

        statistic = Statistic.query.filter_by(project_id=project_id).first()
        statistic.ui_performance_test_runs += 1
        statistic.commit()

        return response
