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

import hashlib
import operator
from json import loads
from datetime import datetime
from sqlalchemy import or_, and_
from flask import request
from flask_restful import Resource
from galloper.database.models.api_reports import APIReport
from galloper.database.models.project import Project
from galloper.database.models.security_results import SecurityResults
from galloper.database.models.security_reports import SecurityReport
from galloper.database.models.security_details import SecurityDetails
from galloper.data_utils.charts_utils import (requests_summary, requests_hits, avg_responses, summary_table,
                                              get_issues, get_data_from_influx, prepare_comparison_responses,
                                              compare_tests, create_benchmark_dataset)

from galloper.dal.influx_results import get_test_details, delete_test_data
from galloper.utils.api_utils import build_req_parser


class ReportAPI(Resource):
    get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args")
    )
    delete_rules = (
        dict(name="id[]", type=int, action="append", location="args"),
    )
    put_rules = (
        dict(name="build_id", type=str, location="json"),
        dict(name="test_name", type=str, location="json"),
        dict(name="lg_type", type=str, location="json"),
        dict(name="missed", type=int, location="json")
    )
    post_rules = put_rules + (
        dict(name="start_time", type=str, location="json"),
        dict(name="duration", type=float, location="json"),
        dict(name="vusers", type=int, location="json"),
        dict(name="environment", type=str, location="json"),
        dict(name="type", type=str, location="json"),
        dict(name="release_id", type=int, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_put = build_req_parser(rules=self.put_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def get(self, project_id: int):
        project = Project.get_object_or_404(pk=project_id)
        reports = []
        args = self._parser_get.parse_args(strict=False)
        limit_ = args.get("limit")
        offset_ = args.get("offset")
        res = []
        total = 0
        if args.get("sort"):
            sort_rule = getattr(getattr(APIReport, args["sort"]), args["order"])()
        else:
            sort_rule = APIReport.id.asc()
        if not args.get('search') and not args.get('filter'):
            total = APIReport.query.filter(APIReport.project_id == project.id).order_by(sort_rule).count()
            res = APIReport.query.filter(
                APIReport.project_id == project.id
            ).order_by(sort_rule).limit(limit_).offset(offset_).all()
        elif args.get("search"):
            search_args = f"%{args['search']}%"
            filter_ = and_(APIReport.project_id == project.id,
                           or_(APIReport.name.like(search_args),
                               APIReport.environment.like(search_args),
                               APIReport.release_id.like(search_args),
                               APIReport.type.like(search_args)))
            res = APIReport.query.filter(filter_).order_by(sort_rule).limit(limit_).offset(offset_).all()
            total = APIReport.query.order_by(sort_rule).filter(filter_).count()
        elif args.get("filter"):
            filter_ = list()
            filter_.append(operator.eq(APIReport.project_id, project.id))
            for key, value in loads(args.get("filter")).items():
                filter_.append(operator.eq(getattr(APIReport, key), value))
            filter_ = and_(*tuple(filter_))
            res = APIReport.query.filter(filter_).order_by(sort_rule).limit(limit_).offset(offset_).all()
            total = APIReport.query.order_by(sort_rule).filter(filter_).count()
        for each in res:
            each_json = each.to_json()
            each_json["start_time"] = each_json["start_time"].replace("T", " ").split(".")[0]
            each_json["duration"] = int(each_json["duration"])
            try:
                each_json["failure_rate"] = round((each_json["failures"] / each_json["total"]) * 100, 2)
            except ZeroDivisionError:
                each_json["failure_rate"] = 0
            reports.append(each_json)
        return {"total": total, "rows": reports}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        report = APIReport(name=args["test_name"],
                           project_id=project.id,
                           environment=args["environment"],
                           type=args["type"],
                           end_time="",
                           start_time=args["start_time"],
                           failures=0,
                           total=0,
                           thresholds_missed=0,
                           throughput=0,
                           vusers=args["vusers"],
                           pct95=0,
                           duration=args["duration"],
                           build_id=args["build_id"],
                           lg_type=args["lg_type"],
                           onexx=0,
                           twoxx=0,
                           threexx=0,
                           fourxx=0,
                           fivexx=0,
                           requests="",
                           release_id=args.get("release_id"))
        report.insert()
        return {"message": "created"}

    def put(self, project_id: int):
        args = self._parser_put.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        test_data = get_test_details(build_id=args["build_id"], test_name=args["test_name"], lg_type=args["lg_type"])
        report = APIReport.query.filter(
            and_(APIReport.project_id == project.id, APIReport.build_id == args["build_id"])
        ).first()
        report.end_time = test_data["end_time"]
        report.start_time = test_data["start_time"]
        report.failures = test_data["failures"]
        report.total = test_data["total"]
        report.thresholds_missed = args.get("missed", 0)
        report.throughput = test_data["throughput"]
        report.pct95 = test_data["pct95"]
        report.onexx = test_data["1xx"]
        report.twoxx = test_data["2xx"]
        report.threexx = test_data["3xx"]
        report.fourxx = test_data["4xx"]
        report.fivexx = test_data["5xx"]
        report.requests = ";".join(test_data["requests"])
        report.commit()
        return {"message": "updated"}

    def delete(self, project_id: int):
        args = self._parser_delete.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        query_result = APIReport.query.filter(
            and_(APIReport.project_id == project.id, APIReport.id.in_(args["id[]"]))
        ).all()
        for each in query_result:
            delete_test_data(each.build_id, each.name, each.lg_type)
            each.delete()
        return {"message": "deleted"}


class ReportChartsAPI(Resource):
    get_rules = (
        dict(name="low_value", type=float, default=0, location="args"),
        dict(name="high_value", type=float, default=100, location="args"),
        dict(name="start_time", type=str, default="", location="args"),
        dict(name="end_time", type=str, default="", location="args"),
        dict(name="aggregator", type=str, default="auto", location="args"),
        dict(name="sampler", type=str, default="REQUEST", location="args"),
        dict(name="metric", type=str, default="", location="args"),
        dict(name="scope", type=str, default="", location="args"),
        dict(name="build_id", type=str, location="args"),
        dict(name="test_name", type=str, location="args"),
        dict(name="lg_type", type=str, location="args")
    )
    mapping = {
        "requests": {
            "summary": requests_summary,
            "hits": requests_hits,
            "average": avg_responses,
            "table": summary_table,
            "data": get_data_from_influx
        },
        "errors": {
            "table": get_issues
        }
    }

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, source: str, target: str):
        args = self._parser_get.parse_args(strict=False)
        return self.mapping[source][target](args)


class ReportsCompareAPI(Resource):
    get_rules = (
        dict(name="low_value", type=float, default=0, location="args"),
        dict(name="high_value", type=float, default=100, location="args"),
        dict(name="start_time", type=str, default="", location="args"),
        dict(name="end_time", type=str, default="", location="args"),
        dict(name="aggregator", type=str, default="auto", location="args"),
        dict(name="sampler", type=str, default="REQUEST", location="args"),
        dict(name="metric", type=str, default="", location="args"),
        dict(name="scope", type=str, default="", location="args"),
        dict(name="id[]", action="append", location="args"),
        dict(name="request", type=str, default="", location="args"),
        dict(name="calculation", type=str, default="", location="args"),
        dict(name="aggregator", type=str, default="1s", location="args")
    )
    mapping = {
        "data": prepare_comparison_responses,
        "tests": compare_tests,
        "benchmark": create_benchmark_dataset
    }

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, target: str):
        args = self._parser_get.parse_args(strict=False)
        return self.mapping[target](args)


class SecurityReportAPI(Resource):
    get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
    )
    delete_rules = (
        dict(name="id[]", type=int, action="append", location="args"),
    )
    post_rules = (
        dict(name="project_name", type=str, location="json"),
        dict(name="app_name", type=str, location="json"),
        dict(name="scan_time", type=float, location="json"),
        dict(name="dast_target", type=str, location="json"),
        dict(name="sast_code", type=str, location="json"),
        dict(name="scan_type", type=str, location="json"),
        dict(name="findings", type=int, location="json"),
        dict(name="false_positives", type=int, location="json"),
        dict(name="excluded", type=int, location="json"),
        dict(name="info_findings", type=int, location="json"),
        dict(name="environment", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def get(self, project_id):
        reports = []
        args = self._parser_get.parse_args(strict=False)
        search_ = args.get("search")
        limit_ = args.get("limit")
        offset_ = args.get("offset")
        if args.get("sort"):
            sort_rule = getattr(getattr(SecurityResults, args["sort"]), args["order"])()
        else:
            sort_rule = SecurityResults.id.desc()
        if not args.get("search") and not args.get("sort"):
            total = SecurityResults.query.filter_by(project_id=project_id).order_by(sort_rule).count()
            res = SecurityResults.query.filter_by(project_id=project_id).\
                order_by(sort_rule).limit(limit_).offset(offset_).all()
        else:
            filter_ = and_(SecurityResults.project_id==project_id,
                      or_(SecurityResults.project_name.like(f"%{search_}%"),
                          SecurityResults.app_name.like(f"%{search_}%"),
                          SecurityResults.scan_type.like(f"%{search_}%"),
                          SecurityResults.environment.like(f"%{search_}%")))
            res = SecurityResults.query.filter(filter_).order_by(sort_rule).limit(limit_).offset(offset_).all()
            total = SecurityResults.query.filter(filter_).order_by(sort_rule).count()
        for each in res:
            each_json = each.to_json()
            each_json["scan_time"] = each_json["scan_time"].replace("T", " ").split(".")[0]
            each_json["scan_duration"] = float(each_json["scan_duration"])
            reports.append(each_json)
        return {"total": total, "rows": reports}

    def delete(self, project_id: int):
        args = self._parser_delete.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        for each in SecurityReport.query.filter(
            and_(SecurityReport.project_id == project.id, SecurityReport.report_id.in_(args["id[]"]))
        ).order_by(SecurityReport.id.asc()).all():
            each.delete()
        for each in SecurityResults.query.filter(
            SecurityResults.id.in_(args["id[]"])
        ).order_by(SecurityResults.id.asc()).all():
            each.delete()
        return {"message": "deleted"}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_object_or_404(pk=project_id)
        report = SecurityResults(scan_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                 project_id=project.id,
                                 scan_duration=args["scan_time"],
                                 project_name=args["project_name"],
                                 app_name=args["app_name"],
                                 dast_target=args["dast_target"],
                                 sast_code=args["sast_code"],
                                 scan_type=args["scan_type"],
                                 findings=args["findings"],
                                 false_positives=args["false_positives"],
                                 excluded=args["excluded"],
                                 info_findings=args["info_findings"],
                                 environment=args["environment"])
        report.insert()
        return {"id": report.id}


class FindingsAPI(Resource):
    get_rules = (
        dict(name="id", type=int, location="args"),
        dict(name="type", type=str, location="args")
    )
    put_rules = (
        dict(name="id", type=int, location="json"),
        dict(name="action", type=str, location="json"),
        dict(name="issue_id", type=int, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_put = build_req_parser(rules=self.put_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        if args["type"] == "false_positives":
            filt = and_(SecurityReport.project_id == project_id,
                        SecurityReport.report_id == args["id"],
                        SecurityReport.false_positive == 1)
        elif args["type"] == "findings":
            filt = and_(SecurityReport.project_id == project_id,
                        SecurityReport.report_id == args["id"],
                        SecurityReport.info_finding == 0,
                        SecurityReport.false_positive == 0,
                        SecurityReport.excluded_finding == 0)
        elif args["type"] == "info_findings":
            filt = and_(SecurityReport.project_id == project_id,
                        SecurityReport.report_id == args["id"],
                        SecurityReport.info_finding == 1)
        elif args["type"] == "excluded_finding":
            filt = and_(SecurityReport.project_id == project_id,
                        SecurityReport.report_id == args["id"],
                        SecurityReport.excluded_finding == 1)
        else:
            filt = and_(SecurityReport.project_id == project_id,
                        SecurityReport.report_id == args["id"])
        issues = SecurityReport.query.filter(filt).all()
        results = []
        for issue in issues:
            _res = issue.to_json()
            _res["details"] = SecurityDetails.query.filter_by(id=_res["details"]).first().details
            results.append(_res)
        return results

    def post(self, project_id: int):
        finding_db = None
        for finding in request.json:
            md5 = hashlib.md5(finding["details"].encode("utf-8")).hexdigest()
            hash_id = SecurityDetails.query.filter(
                and_(SecurityDetails.project_id == project_id, SecurityDetails.detail_hash == md5)
            ).first()
            if not hash_id:
                hash_id = SecurityDetails(detail_hash=md5, project_id=project_id, details=finding["details"])
                hash_id.insert()
            # Verify issue is false_positive or ignored
            finding["details"] = hash_id.id
            finding['project_id'] = project_id
            entrypoints = ""
            if finding.get("endpoints"):
                for each in finding.get("endpoints"):
                    if isinstance(each, list):
                        entrypoints += "<br />".join(each)
                    else:
                        entrypoints += f"<br />{each}"
            finding["endpoints"] = entrypoints
            if not (finding["false_positive"] == 1 or finding["excluded_finding"] == 1):
                # TODO: add validation that finding is a part of project, applicaiton. etc.
                issues = SecurityReport.query.filter(
                    and_(SecurityReport.issue_hash == finding["issue_hash"],
                         or_(SecurityReport.false_positive == 1,
                             SecurityReport.excluded_finding == 1)
                         )).all()
                false_positive = sum(issue.false_positive for issue in issues)
                excluded_finding = sum(issue.excluded_finding for issue in issues)
                finding["false_positive"] = 1 if false_positive > 0 else 0
                finding["excluded_finding"] = 1 if excluded_finding > 0 else 0
            finding_db = SecurityReport(**finding)
            finding_db.add()
        if finding_db:
            finding_db.commit()

    def put(self, project_id: int):
        args = self._parser_put.parse_args(strict=False)
        issue_hash = SecurityReport.query.filter(and_(SecurityReport.project_id == project_id,
                                                      SecurityReport.id == args["issue_id"])
                                                 ).first().issue_hash
        if args["action"] in ("false_positive", "excluded_finding"):
            upd = {args["action"]: 1}
        else:
            upd = {"false_positive": 0, "info_finding": 0}
        # TODO: add validation that finding is a part of project, applicaiton. etc.
        SecurityReport.query.filter(and_(
            SecurityReport.project_id == project_id,
            SecurityReport.issue_hash == issue_hash)
        ).update(upd)
        SecurityReport.commit()
        return {"message": "accepted"}


class FindingsAnalysisAPI(Resource):
    get_rules = (
        dict(name="project_name", type=str, location="args"),
        dict(name="app_name", type=str, location="args"),
        dict(name="scan_type", type=str, location="args"),
        dict(name="type", type=str, default="false-positive", location="args")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        projects_filter = and_(SecurityResults.project_id == project_id,
                               SecurityResults.project_name == args["project_name"],
                               SecurityResults.app_name == args["app_name"],
                               SecurityResults.scan_type == args["scan_type"])
        ids = SecurityResults.query.filter(projects_filter).all()
        ids = [each.id for each in ids]
        hashs = SecurityReport.query.filter(
            and_(SecurityReport.false_positive == 1, SecurityReport.report_id.in_(ids))
            ).with_entities(SecurityReport.issue_hash).distinct()
        return [_.issue_hash for _ in hashs]
