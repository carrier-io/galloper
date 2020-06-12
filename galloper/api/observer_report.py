from datetime import datetime

from flask_restful import Resource

from galloper.database.models.project import Project
from galloper.database.models.ui_report import UIReport
from galloper.utils.api_utils import build_req_parser


class UIReportsAPI(Resource):
    post_rules = (
        dict(name="test_name", type=str, location="json"),
        dict(name="time", type=str, location="json"),
        dict(name="browser_name", type=str, location="json"),
        dict(name="env", type=str, location="json"),
        dict(name="base_url", type=str, location="json"),
        dict(name="loops", type=int, location="json"),
        dict(name="aggregation", type=str, location="json")
    )

    put_rules = (
        dict(name="report_id", type=str, location="json"),
        dict(name="time", type=str, location="json"),
        dict(name="visited_pages", type=int, default=0, location="json"),
        dict(name="thresholds_total", type=int, location="json"),
        dict(name="thresholds_failed", type=int, location="json"),
        dict(name="exception", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_put = build_req_parser(rules=self.put_rules)

    def post(self, project_id: int):
        args = self._parser_post.parse_args()
        project = Project.query.get_or_404(project_id)

        report = UIReport(
            name=args["test_name"],
            project_id=project.id,
            start_time=args["time"],
            is_active=True,
            browser=args["browser_name"],
            environment=args["env"],
            base_url=args["base_url"],
            loops=args["loops"],
            aggregation=args["aggregation"]
        )

        report.insert()

        return report.to_json()

    def put(self, project_id: int):
        args = self._parser_put.parse_args()

        report = UIReport.query.filter_by(project_id=project_id, id=args['report_id']).first_or_404()
        report.is_active = False
        report.stop_time = args["time"]
        report.visited_pages = args["visited_pages"]
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
