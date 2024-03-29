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


from datetime import datetime, timezone
from json import loads
from flask_restful import Resource
from sqlalchemy import and_
from statistics import mean, harmonic_mean
from uuid import uuid4
from galloper.dal.influx_results import get_test_details, delete_test_data, get_aggregated_test_results,\
    get_tps, get_errors, get_response_time_per_test, get_backend_users, get_backend_requests
from galloper.data_utils.charts_utils import (
    requests_summary, requests_hits, avg_responses, summary_table, get_issues, get_data_from_influx,
    prepare_comparison_responses, compare_tests, create_benchmark_dataset
)
from galloper.database.models.api_reports import APIReport
from galloper.database.models.api_baseline import APIBaseline
from galloper.database.models.performance_tests import PerformanceTests
from galloper.database.models.project import Project
from galloper.database.models.statistic import Statistic
from galloper.database.models.project_quota import ProjectQuota
from galloper.api.base import get, run_task
from galloper.utils.api_utils import build_req_parser
from galloper.constants import str_to_timestamp
from galloper.data_utils import arrays
from galloper.dal.vault import get_project_secrets, get_project_hidden_secrets


class ReportAPI(Resource):
    get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args"),
        dict(name="report_id", type=int, default=None, location="args")
    )
    delete_rules = (
        dict(name="id[]", type=int, action="append", location="args"),
    )
    put_rules = (
        dict(name="build_id", type=str, location="json"),
        dict(name="test_name", type=str, location="json"),
        dict(name="lg_type", type=str, location="json"),
        dict(name="missed", type=int, location="json"),
        dict(name="status", type=str, location="json"),
        dict(name="response_times", type=str, location="json"),
        dict(name="duration", type=float, location="json"),
        dict(name="vusers", type=int, location="json")
    )
    post_rules = put_rules + (
        dict(name="start_time", type=str, location="json"),
        dict(name="environment", type=str, location="json"),
        dict(name="type", type=str, location="json"),
        dict(name="release_id", type=int, location="json"),
        dict(name="test_id", type=str, default=None, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_put = build_req_parser(rules=self.put_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        if args.get("report_id"):
            report = APIReport.query.filter_by(project_id=project_id, id=args.get("report_id")).first().to_json()
            return report
        reports = []
        total, res = get(project_id, args, APIReport)
        for each in res:
            each_json = each.to_json()
            each_json["start_time"] = each_json["start_time"].replace("T", " ").split(".")[0]
            each_json["duration"] = int(each_json["duration"] if each_json["duration"] else 0)
            try:
                each_json["failure_rate"] = round((each_json["failures"] / each_json["total"]) * 100, 2)
            except ZeroDivisionError:
                each_json["failure_rate"] = 0
            reports.append(each_json)
        return {"total": total, "rows": reports}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        if not ProjectQuota.check_quota(project_id=project_id, quota='performance_test_runs'):
            return {"Forbidden": "The number of performance test runs allowed in the project has been exceeded"}
        report = APIReport(name=args["test_name"],
                           status=args["status"],
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
                           pct50=0,
                           pct75=0,
                           pct90=0,
                           pct95=0,
                           pct99=0,
                           _max=0,
                           _min=0,
                           mean=0,
                           duration=args["duration"],
                           build_id=args["build_id"],
                           lg_type=args["lg_type"],
                           onexx=0,
                           twoxx=0,
                           threexx=0,
                           fourxx=0,
                           fivexx=0,
                           requests="",
                           release_id=args.get("release_id"),
                           test_uid=args.get("test_id"))
        report.insert()
        statistic = Statistic.query.filter_by(project_id=project_id).first()
        setattr(statistic, 'performance_test_runs', Statistic.performance_test_runs + 1)
        statistic.commit()
        return report.to_json()

    def put(self, project_id: int):
        args = self._parser_put.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        test_data = get_test_details(project_id=project_id, build_id=args["build_id"], test_name=args["test_name"],
                                     lg_type=args["lg_type"])
        response_times = loads(args["response_times"])
        report = APIReport.query.filter(
            and_(APIReport.project_id == project.id, APIReport.build_id == args["build_id"])
        ).first()
        report.end_time = test_data["end_time"]
        report.start_time = test_data["start_time"]
        report.failures = test_data["failures"]
        report.total = test_data["total"]
        report.thresholds_missed = args.get("missed", 0)
        report.throughput = test_data["throughput"]
        report.pct50 = response_times["pct50"]
        report.pct75 = response_times["pct75"]
        report.pct90 = response_times["pct90"]
        report.pct95 = response_times["pct95"]
        report.pct99 = response_times["pct99"]
        report._max = response_times["max"]
        report._min = response_times["min"]
        report.mean = response_times["mean"]
        report.onexx = test_data["1xx"]
        report.twoxx = test_data["2xx"]
        report.threexx = test_data["3xx"]
        report.fourxx = test_data["4xx"]
        report.fivexx = test_data["5xx"]
        report.requests = ";".join(test_data["requests"])
        report.status = args["status"]
        report.vusers = args["vusers"]
        report.duration = args["duration"]
        report.commit()
        return {"message": "updated"}

    def delete(self, project_id: int):
        args = self._parser_delete.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        query_result = APIReport.query.filter(
            and_(APIReport.project_id == project.id, APIReport.id.in_(args["id[]"]))
        ).all()
        for each in query_result:
            delete_test_data(each.build_id, each.name, each.lg_type)
            baseline = APIBaseline.query.filter_by(project_id=project.id, report_id=each.id).first()
            if baseline:
                baseline.delete()
            each.delete()
        return {"message": "deleted"}


class ReportPostProcessingAPI(Resource):
    get_rules = (
        dict(name="build_id", type=str, location="args"),
    )
    post_rules = (
        dict(name="report_id", type=int, location="json"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        report = APIReport.query.filter_by(project_id=project.id, build_id=args["build_id"]).first()

        return {"status": report.status}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        report = APIReport.query.filter_by(project_id=project_id, id=args.get("report_id")).first().to_json()
        event = {
            "galloper_url": "{{secret.galloper_url}}",
            "project_id": project.id,
            "token": "{{secret.auth_token}}",
            "report_id": args["report_id"],
            "influx_host": "{{secret.influx_ip}}",
            "influx_user": "{{secret.influx_user}}",
            "influx_password": "{{secret.influx_password}}",
            "config_file": "{}",
            "bucket": str(report["name"]).lower().replace(" ", "").replace("_", "").replace("-", ""),
            "prefix": f'test_results_{uuid4()}_',
        }
        task = PerformanceTests.query.filter(and_(PerformanceTests.project_id == project.id,
                                                  PerformanceTests.test_uid == report["test_uid"])).first()
        event["email_recipients"] = task.emails
        integration = []
        reporters = {
            "jira": "jira",
            "report_portal": "rp",
            "email": "email",
            "azure_devops": "ado"
        }
        for each in ["jira", "report_portal", "email", "azure_devops"]:
            if reporters[each] in task.reporting:
                integration.append(each)
        junit = True if "junit" in task.reporting else False
        event["integration"] = integration
        event["junit"] = junit
        secrets = get_project_secrets(project_id)
        if "post_processor_id" not in secrets:
            secrets = get_project_hidden_secrets(project_id)

        return run_task(project.id, event, secrets["post_processor_id"])


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
        dict(name="env", type=str, location="args")
    )
    post_rules = (
        dict(name="test_name", type=str, location="json"),
        dict(name="build_id", type=str, location="json"),
        dict(name="env", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        baseline = APIBaseline.query.filter_by(project_id=project.id, test=args.get("test_name"),
                                               environment=args.get("env")).first()
        test = baseline.summary if baseline else []
        report_id = baseline.report_id if baseline else 0
        return {"baseline": test, "report_id": report_id}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        report_id = APIReport.query.filter_by(project_id=project_id, name=args['test_name'],
                                              build_id=args['build_id']).first().to_json()['id']
        baseline = APIBaseline.query.filter_by(project_id=project.id, test=args.get("test_name"),
                                               environment=args.get("env")).first()
        if baseline:
            baseline.delete()
        test = get_aggregated_test_results(args['test_name'], args['build_id'])
        summary = []
        for req in test[0]:
            summary.append(req)
        baseline = APIBaseline(test=args["test_name"],
                               environment=args["env"],
                               project_id=project.id,
                               report_id=report_id,
                               summary=summary)
        baseline.insert()
        return {"message": "baseline is set"}


class TestSaturation(Resource):
    _rules = (
        dict(name="test_id", type=int, location="args"),
        dict(name="project_id", type=int, location="args"),
        dict(name="wait_till", type=int, default=600, location="args"),
        dict(name='sampler', type=str, location="args", required=True),
        dict(name='request', type=str, location="args", required=True),
        dict(name='max_errors', type=float, default=100.0, location="args"),
        dict(name='aggregation', type=str, default="1m", location="args"),
        dict(name='status', type=str, default='ok', location="args"),
        dict(name="calculation", type=str, default="sum", location="args"),
        dict(name="deviation", type=float, default=0.02, location="args"),
        dict(name="max_deviation", type=float, default=0.05, location="args"),
        dict(name="extended_output", type=bool, default=False, location="args"),
        dict(name="u", type=int, action="append", location="args"),
        dict(name="u_aggr", type=int, default=5, location="args"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self._rules)

    @staticmethod
    def part(data, part):
        data = sorted(data)
        n = len(data)
        if n <= part or part == 1:
            return data[-1]
        parts = n // part
        return data[parts * (part-1)]

    def get(self):
        args = self._parser_get.parse_args(strict=False)
        project = Project.get_or_404(args["project_id"])
        report = APIReport.query.filter(
            and_(APIReport.id == args['test_id'], APIReport.project_id == project.id)
        ).first()
        start_time = str_to_timestamp(report.start_time)
        if report.end_time:
            current_time = str_to_timestamp(report.end_time)
        else:
            current_time = datetime.utcnow().timestamp()
        str_start_time = datetime.fromtimestamp(start_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        str_current_time = datetime.fromtimestamp(current_time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        duration_till_now = current_time - start_time
        if duration_till_now < args['wait_till']:
            return {"message": "not enough results", "code": 0}
        ts_array, data, users = get_tps(report.build_id, report.name, report.lg_type, str_start_time, str_current_time,
                                        "1s", args["sampler"], scope=args["request"], status=args["status"])
        users = list(users["users"].values())
        _tmp = []
        tps = list()
        usrs = list()
        errors = list()
        if 'm' in args["aggregation"]:
            ss = int(args["aggregation"].replace('m', '')) * 60
        elif 's' in args["aggregation"]:
            ss = int(args["aggregation"].replace('s', ''))
        else:
            ss = 60
        calculation_mapping = {
            'max': max,
            'min': min,
            'mean': mean,
            'sum': sum
        }
        calculation = args['calculation'] if args['calculation'] in list(calculation_mapping.keys()) else 'sum'
        for index, _ in enumerate(data["responses"].values()):
            if isinstance(_, int):
                _tmp.append(_)
            if len(_tmp) and (len(_tmp) % ss) == 0:
                tps.append(round(calculation_mapping[calculation](_tmp)))
                usrs.append(users[index])
                _tmp = []
        if _tmp:
            tps.append(round(calculation_mapping[calculation](_tmp)))
            usrs.append(users[-1])
            _tmp = []
        _, data, _ = get_errors(report.build_id, report.name, report.lg_type, str_start_time, str_current_time,
                                args["aggregation"], args["sampler"], scope=args["request"])
        for each in data['errors'].values():
            if each:
                errors.append(each)
        total = int(get_response_time_per_test(report.build_id, report.name, report.lg_type, args["sampler"],
                                               args["request"], "total"))
        error_rate = float(sum(errors))/float(total) * 100
        try:
            max_tp, user_index = arrays.non_decreasing(tps[:-1], deviation=args["deviation"], val=True)
            max_users = args["u_aggr"] * round(usrs[user_index]/args["u_aggr"])
            max_tp = tps[user_index]
            current_users = args["u_aggr"] * round(usrs[user_index+1]/args["u_aggr"])
            if current_users == max_users:
                current_users += args["u_aggr"]
            if current_users == 0:
                current_users = max_users + args["u_aggr"]
            if current_users < max_users:
                current_users = max_users + args["u_aggr"]
        except TypeError:
            return {"message": "not enough results", "code": 0}
        except IndexError:
            if error_rate > args["max_errors"]:
                return {"message": f"error rate reached 100% for {args['request']} transaction", "errors_rate": 100.0,
                        "code": 1}
            else:
                return {"message": "not enough results", "code": 0}

        response = {
            "ts": ts_array[-1],
            "max_users": max_users,
            "max_throughput": round(max_tp, 2),
            "current_users": current_users,
            "current_throughput": round(tps[user_index], 2),
            "errors_rate": round(error_rate, 2)
        }
        if args["u"]:
            user_array = args["u"]
            if max_users not in user_array:
                user_array.append(max_users)
            if current_users not in user_array:
                user_array.append(current_users)
            user_array.sort()
            user_array.reverse()
            uber_array = {}
            _, users = get_backend_users(report.build_id, report.lg_type, str_start_time, str_current_time, "1s")
            u = user_array.pop()
            start_time = _[0]
            end_time = _[-1]
            response["test_start"] = start_time
            response["test_end"] = end_time
            for key, value in users["users"].items():
                if value > u and max_users >= u:
                    _, data, _ = get_tps(report.build_id, report.name, report.lg_type, start_time, key,
                                         "1s", args["sampler"], scope=args["request"],
                                         status=args["status"])
                    tp = [0 if v is None else v for v in list(data['responses'].values())[:-1]]
                    array_size = len(tp)
                    tp = calculation_mapping[calculation](tp) if len(tp) != 0 else 0
                    if array_size != ss:
                        coefficient = float(array_size/ss)
                    else:
                        coefficient = 1
                    tp = int(tp / coefficient)
                    if round(tp, 2) > response["max_throughput"] and u != current_users:
                        response["max_throughput"] = round(tp, 2)
                        response["max_users"] = u
                        current_users = u + args["u_aggr"]
                        response["current_users"] = current_users
                    _, data, _ = get_backend_requests(report.build_id, report.name, report.lg_type,
                                                      start_time, key, "1s", args["sampler"], scope=args["request"],
                                                      status=args["status"])
                    rt = []
                    started = False
                    for v in list(data['response'].values())[:-1]:
                        if v and v > 0:
                            started = True
                        if started and v and v > 0:
                            rt.append(v)
                    rt = self.part(rt, args["u_aggr"]) if rt else 0
                    uber_array[str(u)] = {
                        "throughput": round(tp, 2),
                        "response_time": round(rt, 2)
                    }
                    start_time = key
                    u = user_array.pop()
            if str(response["max_users"]) not in list(uber_array.keys()):
                _, data, _ = get_backend_requests(report.build_id, report.name, report.lg_type,
                                                  start_time, end_time, "1s", args["sampler"], scope=args["request"],
                                                  status=args["status"])
                rt = []
                started = False
                for v in list(data['response'].values())[:-1]:
                    if v and v > 0:
                        started = True
                    if started and v and v > 0:
                        rt.append(v)
                rt = self.part(rt, args["u_aggr"]) if rt else 0
                uber_array[str(max_users)] = {
                    "throughput": response["max_throughput"],
                    "response_time": round(rt, 2)
                }
            else:
                uber_array[str(response["max_users"])]["throughput"] = response["max_throughput"]
            if str(current_users) not in list(uber_array.keys()):

                uber_array[str(current_users)] = {
                    "throughput": response["current_throughput"],
                    "response_time": uber_array.get(str(max_users), list(uber_array.values())[-1])["response_time"]
                }
            else:
                uber_array[str(current_users)]["throughput"] = response["current_throughput"]
            response["benchmark"] = uber_array
        if args["extended_output"]:
            response["details"] = {}
            response["tps"] = tps
            for index, value in enumerate(usrs):
                if not response["details"].get(value) or response["details"][value] > tps[index]:
                    response["details"][value] = tps[index]
        if (arrays.non_decreasing(tps[:-1], deviation=args["deviation"]) and
                error_rate <= args["max_errors"] and
                response["current_throughput"] * (1 + args["max_deviation"]) >= response["max_throughput"]):
            response["message"] = "proceed"
            response["code"] = 0
            return response
        else:
            response["message"] = "saturation"
            response["code"] = 1
            return response




