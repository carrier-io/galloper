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

import operator
from json import loads
from datetime import datetime, timezone

from flask_restful import Resource
from sqlalchemy import or_, and_
from werkzeug.exceptions import Forbidden

from galloper.dal.influx_results import get_test_details, delete_test_data, get_aggregated_test_results, set_baseline,\
    get_baseline, delete_baseline, get_tps, get_errors, get_backend_requests, get_response_time_per_test
from galloper.data_utils.charts_utils import (
    requests_summary, requests_hits, avg_responses, summary_table, get_issues, get_data_from_influx,
    prepare_comparison_responses, compare_tests, create_benchmark_dataset
)
from galloper.database.models.api_reports import APIReport
from galloper.database.models.project import Project
from galloper.database.models.statistic import Statistic
from galloper.utils.api_utils import build_req_parser
from galloper.constants import str_to_timestamp
from galloper.data_utils import arrays

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

    def __calcualte_limit(self, limit, total):
        return len(total) if limit == 'All' else limit

    def get(self, project_id: int):
        project = Project.query.get_or_404(project_id)
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
            ).order_by(sort_rule).limit(self.__calcualte_limit(limit_, total)).offset(offset_).all()
        elif args.get("search"):
            search_args = f"%{args['search']}%"
            filter_ = and_(APIReport.project_id == project.id,
                           or_(APIReport.name.like(search_args),
                               APIReport.environment.like(search_args),
                               APIReport.type.like(search_args)))
            total = APIReport.query.order_by(sort_rule).filter(filter_).count()
            res = APIReport.query.filter(filter_).order_by(sort_rule).limit(
                self.__calcualte_limit(limit_, total)).offset(offset_).all()
        elif args.get("filter"):
            filter_ = list()
            filter_.append(operator.eq(APIReport.project_id, project.id))
            for key, value in loads(args.get("filter")).items():
                filter_.append(operator.eq(getattr(APIReport, key), value))
            filter_ = and_(*tuple(filter_))
            total = APIReport.query.order_by(sort_rule).filter(filter_).count()
            res = APIReport.query.filter(filter_).order_by(sort_rule).limit(
                self.__calcualte_limit(limit_, total)).offset(offset_).all()
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
        project = Project.query.get_or_404(project_id)
        if not project.performance_enabled:
            raise Forbidden(description="Performance tests are not allowed for this project")
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
        statistic = Statistic.query.filter_by(project_id=project_id).first()
        setattr(statistic, 'performance_test_runs', Statistic.performance_test_runs + 1)
        statistic.commit()
        return report.to_json()

    def put(self, project_id: int):
        args = self._parser_put.parse_args(strict=False)
        project = Project.query.get_or_404(project_id)
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
        project = Project.query.get_or_404(project_id)
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
        dict(name="lg_type", type=str, location="args"),
        dict(name='status', type=str, default='all', location="args")
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
        dict(name="aggregator", type=str, default="1s", location="args"),
        dict(name='status', type=str, default='all', location="args")
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


class BaselineAPI(Resource):
    get_rules = (
        dict(name="test_name", type=str, location="args"),
    )
    post_rules = (
        dict(name="test_name", type=str, location="json"),
        dict(name="build_id", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        test = get_baseline(args['test_name'])
        test = test[0] if len(test) > 0 else []
        return {"baseline": test}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        report_id = APIReport.query.filter_by(project_id=project_id, name=args['test_name'],
                                              build_id=args['build_id']).first().to_json()['id']
        baseline = get_baseline(args['test_name'])
        if baseline:
            delete_baseline(baseline[0][0]['build_id'])
        test = get_aggregated_test_results(args['test_name'], args['build_id'])
        for req in test[0]:
            req['report_id'] = report_id
            set_baseline(req)
        return {"message": "baseline is set"}


class TestSaturation(Resource):
    _rules = (
        dict(name="test_id", type=int, location="args"),
        dict(name="project_id", type=int, location="args"),
        dict(name="wait_till", type=int, default=600, location="args"),
        dict(name='sampler', type=str, location="args", required=True),
        dict(name='request', type=str, location="args", required=True),
        dict(name='max_errors', type=float, default=1.0, location="args"),
        dict(name='aggregation', type=str, default="1m", location="args"),
        dict(name='status', type=str, default='ok', location="args"),
        dict(name="calculation", type=str, default="pct95", location="args"),
        dict(name="deviation", type=float, default=0.05, location="args")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self._rules)

    def get(self):
        args = self._parser_get.parse_args(strict=False)
        project = Project.query.get_or_404(args["project_id"])
        report = APIReport.query.filter(
            and_(APIReport.id == args['test_id'], APIReport.project_id == project.id)
        ).first()
        start_time = str_to_timestamp(report.start_time)
        current_time = datetime.utcnow().timestamp()
        str_start_time = datetime.fromtimestamp(start_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        str_current_time = datetime.fromtimestamp(current_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        duration_till_now = current_time - start_time
        if duration_till_now < args['wait_till']:
            return {"message": "not enough results", "code": 0}
        _, data, _ = get_tps(report.build_id, report.name, report.lg_type, str_start_time, str_current_time,
                             args["aggregation"], args["sampler"], scope=args["request"], status=args["status"])
        tps = []
        for each in data['responses'].values():
            if each:
                tps.append(each)
        _, data, _ = get_errors(report.build_id, report.name, report.lg_type, str_start_time, str_current_time,
                                args["aggregation"], args["sampler"], scope=args["request"])
        errors = []
        for each in data['errors'].values():
            if each:
                errors.append(each)
        total = int(get_response_time_per_test(report.build_id, report.name, report.lg_type, args["sampler"],
                                               args["request"], "total"))
        error_rate = float(sum(errors))/float(total)
        if arrays.non_decreasing(tps[:-1], deviation=args["deviation"]) and error_rate <= args["max_errors"]:
            return {"message": "proceed", "throughput": max(tps), "errors_rate": error_rate, "code": 0}
        else:
            return {
                "message": "saturation",
                "throughput": max(tps),
                "errors": error_rate,
                "code": 1
            }




