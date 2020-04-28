import operator
from json import loads
from typing import Optional

from flask_restful import Resource
from sqlalchemy import or_, and_

from galloper.database.models.api_reports import APIReport
from galloper.database.models.project import Project
from galloper.constants import str_to_timestamp
from galloper.database.models.ui_report import UIReport
from galloper.database.models.ui_result import UIResult
from galloper.utils.api_utils import build_req_parser
from uuid import uuid4


class VisualReportAPI(Resource):
    get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def __calcualte_limit(self, limit, total):
        return len(total) if limit == 'All' else limit

    def get(self, project_id: int):
        project = Project.query.get_or_404(project_id)
        reports = []
        args = self._parser_get.parse_args(strict=False)
        limit_ = args.get("limit")
        offset_ = args.get("offset")
        from uuid import uuid4
        # expected model

        reports = UIReport.query.filter_by(project_id=project_id).all()

        res = []

        for report in reports:
            results = UIResult.query.filter_by(report_id=report.id).all()

            totals = list(map(lambda x: x.total, results))

            try:
                avg_page_load = sum(totals) / len(totals)
            except ZeroDivisionError:
                avg_page_load = 0

            try:
                thresholds_missed = report.thresholds_failed / report.thresholds_total * 100
            except ZeroDivisionError:
                thresholds_missed = 0

            data = dict(id=report.id, project_id=project_id, name=report.test_name, environment=report.env,
                        browser=report.browser,
                        browser_version="12.2.3", resolution="1380x749", url=report.base_url,
                        end_time=report.stop_time, start_time=report.start_time, duration=report.duration,
                        failures=1, total=10,
                        thresholds_missed=thresholds_missed,
                        avg_page_load=avg_page_load / 1000,
                        avg_step_duration=0.5, build_id=str(uuid4()), release_id=1)

            res.append(data)

        for each in res:
            each["start_time"] = each["start_time"].replace("T", " ").replace("Z", "")
        return {"total": len(res), "rows": res}


class VisualResultAPI(Resource):

    def get(self, project_id: int, report_id: int, action: Optional[str] = "table"):
        _action_mapping = {
            "table": [],
            "chart": {
                "nodes": [
                    {"data": {"id": 'start', "name": 'Start', "bucket": "reports", "file": ""}}
                ],
                "edges": [
                ]
            }
        }

        report = UIReport.query.get_or_404(report_id)
        results = UIResult.query.filter_by(project_id=project_id, report_id=report_id).all()

        table = []
        nodes = _action_mapping["chart"]["nodes"]
        edges = _action_mapping["chart"]["edges"]

        for result in results:
            source_node_id = nodes[-1]["data"]["id"]
            target_node_id = str(uuid4())

            nodes.append({
                "data": {
                    "id": target_node_id,
                    "name": result.name,
                    "file": f"/api/v1/artifacts/{project_id}/reports/{result.file_name}"
                }
            })

            edges.append({
                "data": {"source": source_node_id, "target": target_node_id,
                         "time": f"{round(result.total / 1000, 2)} sec"}
            })

            data = {
                "name": result.name,
                "speed_index": result.speed_index,
                "total_time": round(result.total / 1000, 2),
                "first_bite": result.time_to_first_byte,
                "first_paint": result.time_to_first_paint,
                "content_load": result.dom_content_loading,
                "dom_processing": result.dom_processing,
                "missed_thresholds": result.thresholds_failed,
                "report": f"/api/v1/artifacts/{project_id}/reports/{result.file_name}",
                "actions": []
            }

            actions = []
            for loc in result.locators:
                if loc['target'] == "/":
                    loc['target'] = report.base_url

                actions.append({
                    "action": loc["command"],
                    "locator": loc['target'],
                    "value": loc['value']
                })

            data["actions"] = actions

            table.append(data)

        _action_mapping["table"] = table
        return _action_mapping[action]
