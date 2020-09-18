from uuid import uuid4
from flask_restful import Resource
from json import loads
from flask import request, current_app
from sqlalchemy import and_
from galloper.api.base import get, run_task
from galloper.database.models.project import Project
from galloper.database.models.security_tests import SecurityTestsDAST, SecurityTestsSAST
from galloper.database.models.security_thresholds import SecurityThresholds
from galloper.database.models.statistic import Statistic
from galloper.utils.api_utils import build_req_parser, str2bool


#
# Seed dispatcher
#


class SecuritySeedDispatcher(Resource):
    _get_rules = (
        dict(name="type", type=str, location="args"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)

    def get(self, project_id: int, seed: str):
        """ Get config for seed """
        args = self.get_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        #
        test_type = seed.split("_")[0]
        test_id = seed.split("_")[1]
        #
        if test_type == "dast":
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.test_uid == test_id
            )
            test = SecurityTestsDAST.query.filter(_filter).first()
        #
        if test_type == "sast":
            _filter = and_(
                SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.test_uid == test_id
            )
            test = SecurityTestsSAST.query.filter(_filter).first()
        #
        try:
            thresholds = SecurityThresholds.query.filter(SecurityThresholds.test_uid == test_id).first().to_json(
                exclude_fields=("id", "project_id", "test_name", "test_uid"))
            current_app.logger.info(thresholds)
        except AttributeError:
            thresholds = {}
        return test.configure_execution_json(args.get("type"), execution=True, thresholds=thresholds)


#
# DAST
#


class TestsApiSecurityDAST(Resource):
    _get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args"),
    )

    _post_rules = (
        dict(name="name", type=str, location='form'),
        dict(name="dast_settings", type=str, location='form'),
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
        """ Get existing tests """
        args = self.get_parser.parse_args(strict=False)
        reports = []
        total, res = get(project_id, args, SecurityTestsDAST)
        for each in res:
            reports.append(each.to_json())
        return {"total": total, "rows": reports}

    def post(self, project_id: int):
        """ Create new test """
        current_app.logger.info(request.form)
        args = self.post_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        test = SecurityTestsDAST(
            project_id=project.id,
            test_uid=str(uuid4()),
            name=args["name"],
            dast_settings={
                "project_name": project.name,
                **loads(args["dast_settings"]),
            },
        )
        test.insert()
        current_app.logger.info(test.to_json())
        threshold = SecurityThresholds(
            project_id=project.id,
            test_name=args["name"],
            test_uid=test.test_uid,
            critical=-1, high=-1, medium=-1, low=-1, info=-1,
            critical_life=-1, high_life=-1, medium_life=-1, low_life=-1, info_life=-1)
        threshold.insert()
        return test.to_json(exclude_fields=("id",))

    def delete(self, project_id: int):
        """ Delete existing test """
        args = self.delete_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        query_result = SecurityTestsDAST.query.filter(
            and_(SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.id.in_(args["id[]"]))
        ).all()
        for each in query_result:
            each.delete()
        return {"message": "deleted"}


class TestApiSecurityDAST(Resource):
    _get_rules = (
        dict(name="raw", type=int, default=0, location="args"),
        dict(name="type", type=str, default='cc', location="args"),
        dict(name="exec", type=str2bool, default=False, location="args"),
    )

    _put_rules = (
        dict(name="dast_settings", type=str, required=False, location='json'),
    )

    _post_rules = _put_rules + (
        dict(name="test_type", type=str, required=False, location='json'),
        dict(name="runner", type=str, required=False, location='json'),
        dict(name="type", type=str, default=None, required=False, location='json'),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)
        self.put_parser = build_req_parser(rules=self._put_rules)
        self.post_parser = build_req_parser(rules=self._post_rules)

    def get(self, project_id, test_id):
        """ Get test data """
        args = self.get_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        #
        if isinstance(test_id, int):
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.test_uid == test_id
            )
        test = SecurityTestsDAST.query.filter(_filter).first()
        #
        if args.raw:
            return test.to_json()
        #
        if args["type"] == "docker":
            message = test.configure_execution_json(args.get("type"), execution=args.get("exec"))
        else:  # type = cc
            message = [{"test_id": test.test_uid}]
        #
        return {"config": message}

    def put(self, project_id, test_id):
        """ Update test data """
        args = self.put_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        #
        if isinstance(test_id, int):
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.test_uid == test_id
            )
        task = SecurityTestsDAST.query.filter(_filter).first()
        #
        if args.get("dast_settings", None):
            task.dast_settings = {
                "project_name": project.name,
                **loads(args["dast_settings"]),
            }
        #
        task.commit()
        return task.to_json()

    def post(self, project_id, test_id):
        """ Run test """
        args = self.post_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        #
        if isinstance(test_id, int):
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.test_uid == test_id
            )
        task = SecurityTestsDAST.query.filter(_filter).first()
        #
        execution = bool(args["type"] and args["type"] == "config")
        #
        event = list()
        event.append(task.configure_execution_json("cc", execution=execution))
        #
        if args["type"] and args["type"] == "config":
            return event[0]
        #
        response = run_task(project.id, event)
        response["redirect"] = f"/task/{response['task_id']}/results"
        #
        statistic = Statistic.query.filter_by(project_id=project_id).first()
        statistic.dast_scans += 1
        statistic.commit()
        #
        return response


#
# SAST
#


class TestsApiSecuritySAST(Resource):
    _get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args"),
    )

    _post_rules = (
        dict(name="name", type=str, location='form'),
        dict(name="sast_settings", type=str, location='form'),
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
        """ Get existing tests """
        args = self.get_parser.parse_args(strict=False)
        reports = []
        total, res = get(project_id, args, SecurityTestsSAST)
        for each in res:
            reports.append(each.to_json())
        return {"total": total, "rows": reports}

    def post(self, project_id: int):
        """ Create new test """
        current_app.logger.info(request.form)
        args = self.post_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        test = SecurityTestsSAST(
            project_id=project.id,
            test_uid=str(uuid4()),
            name=args["name"],
            sast_settings={
                "project_name": project.name,
                **loads(args["sast_settings"]),
            },
        )
        test.insert()
        threshold = SecurityThresholds(
            project_id=project.id,
            test_name=args["name"],
            test_uid=test.test_uid,
            critical=-1, high=-1, medium=-1, low=-1, info=-1,
            critical_life=-1, high_life=-1, medium_life=-1, low_life=-1, info_life=-1, )
        threshold.insert()
        current_app.logger.info(test.to_json())
        return test.to_json(exclude_fields=("id",))

    def delete(self, project_id: int):
        """ Delete existing test """
        args = self.delete_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        query_result = SecurityTestsSAST.query.filter(
            and_(SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.id.in_(args["id[]"]))
        ).all()
        for each in query_result:
            each.delete()
        return {"message": "deleted"}


class TestApiSecuritySAST(Resource):
    _get_rules = (
        dict(name="raw", type=int, default=0, location="args"),
        dict(name="type", type=str, default='cc', location="args"),
        dict(name="exec", type=str2bool, default=False, location="args"),
    )

    _put_rules = (
        dict(name="sast_settings", type=str, required=False, location='json'),
    )

    _post_rules = _put_rules + (
        dict(name="test_type", type=str, required=False, location='json'),
        dict(name="runner", type=str, required=False, location='json'),
        dict(name="type", type=str, default=None, required=False, location='json'),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)
        self.put_parser = build_req_parser(rules=self._put_rules)
        self.post_parser = build_req_parser(rules=self._post_rules)

    def get(self, project_id, test_id):
        """ Get test data """
        args = self.get_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        #
        if isinstance(test_id, int):
            _filter = and_(
                SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.test_uid == test_id
            )
        test = SecurityTestsSAST.query.filter(_filter).first()
        #
        if args.raw:
            return test.to_json()
        #
        if args["type"] == "docker":
            message = test.configure_execution_json(args.get("type"), execution=args.get("exec"))
        else:  # type = cc
            message = [{"test_id": test.test_uid}]
        #
        return {"config": message}

    def put(self, project_id, test_id):
        """ Update test data """
        args = self.put_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        #
        if isinstance(test_id, int):
            _filter = and_(
                SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.test_uid == test_id
            )
        task = SecurityTestsSAST.query.filter(_filter).first()
        #
        if args.get("sast_settings", None):
            task.sast_settings = {
                "project_name": project.name,
                **loads(args["sast_settings"]),
            }
        #
        task.commit()
        return task.to_json()

    def post(self, project_id, test_id):
        """ Run test """
        args = self.post_parser.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        #
        if isinstance(test_id, int):
            _filter = and_(
                SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityTestsSAST.project_id == project.id, SecurityTestsSAST.test_uid == test_id
            )
        task = SecurityTestsSAST.query.filter(_filter).first()
        #
        execution = bool(args["type"] and args["type"] == "config")
        #
        event = list()
        event.append(task.configure_execution_json("cc", execution=execution))
        #
        if args["type"] and args["type"] == "config":
            return event[0]
        #
        response = run_task(project.id, event)
        response["redirect"] = f"/task/{response['task_id']}/results"
        #
        statistic = Statistic.query.filter_by(project_id=project_id).first()
        statistic.sast_scans += 1
        statistic.commit()
        #
        return response
