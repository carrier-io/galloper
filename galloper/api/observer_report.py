from datetime import datetime

from flask_restful import Resource

from galloper.database.models.project import Project
from galloper.database.models.ui_report import UIReport
from galloper.utils.api_utils import build_req_parser


class UIReportsAPI(Resource):
    get_rules = (
        dict(name="report_id", type=str, location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="count", type=int, location="args")
    )

    post_rules = (
        dict(name="test_name", type=str, location="json"),
        dict(name="time", type=str, location="json"),
        dict(name="status", type=str, location="json"),
        dict(name="browser_name", type=str, location="json"),
        dict(name="browser_version", type=str, location="json"),
        dict(name="env", type=str, location="json"),
        dict(name="base_url", type=str, location="json"),
        dict(name="loops", type=int, location="json"),
        dict(name="aggregation", type=str, location="json"),
        dict(name="report_id", type=str, location="json")
    )

    put_rules = (
        dict(name="report_id", type=str, location="json"),
        dict(name="time", type=str, location="json"),
        dict(name="status", type=str, location="json"),
        dict(name="thresholds_total", type=int, location="json"),
        dict(name="thresholds_failed", type=int, location="json"),
        dict(name="exception", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_put = build_req_parser(rules=self.put_rules)
        self._parser_get = build_req_parser(rules=self.get_rules)

    def post(self, project_id: int):
        args = self._parser_post.parse_args()

        report = UIReport.query.filter_by(uid=args['report_id']).first()

        if report:
            return report.to_json()

        project = Project.query.get_or_404(project_id)

        report = UIReport(
            uid=args['report_id'],
            name=args["test_name"],
            status=args["status"],
            project_id=project.id,
            start_time=args["time"],
            is_active=True,
            browser=args["browser_name"],
            browser_version=args["browser_version"],
            environment=args["env"],
            base_url=args["base_url"],
            loops=args["loops"],
            aggregation=args["aggregation"]
        )

        report.insert()

        return report.to_json()

    def put(self, project_id: int):
        args = self._parser_put.parse_args()

        report = UIReport.query.filter_by(project_id=project_id, uid=args['report_id']).first_or_404()
        report.is_active = False
        report.stop_time = args["time"]
        report.status = args["status"]
        report.thresholds_total = args["thresholds_total"],
        report.thresholds_failed = args["thresholds_failed"]
        report.duration = self.__diffdates(report.start_time, args["time"]).seconds

        exception = args["exception"]
        if exception:
            report.exception = exception
            report.passed = False

        report.commit()

        return report.to_json()

    def __diffdates(self, d1, d2):
        # Date format: %Y-%m-%d %H:%M:%S
        date_format = '%Y-%m-%d %H:%M:%S'
        return datetime.strptime(d2, date_format) - datetime.strptime(d1, date_format)

    def get(self, project_id):
        args = self._parser_get.parse_args()
        if args['report_id']:
            if isinstance(args['report_id'], int):
                report = UIReport.query.filter_by(project_id=project_id, id=args['report_id']).first_or_404()
            else:
                report = UIReport.query.filter_by(project_id=project_id, uid=args['report_id']).first_or_404()
        else:
            reports = UIReport.query.filter_by(project_id=project_id, name=args['name']).order_by(UIReport.id.desc()).limit(args['count'])
            _reports = []
            for each in reports:
                _reports.append(each.to_json())
            return _reports

        return report.to_json()
