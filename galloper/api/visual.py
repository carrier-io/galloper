from typing import Optional
from uuid import uuid4

from flask_restful import Resource
from sqlalchemy import and_

from galloper.api.base import get
from galloper.data_utils.arrays import get_aggregated_data, closest
from galloper.database.models.project import Project
from galloper.database.models.ui_report import UIReport
from galloper.database.models.ui_result import UIResult
from galloper.utils.api_utils import build_req_parser


class VisualReportAPI(Resource):
    get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="start_time", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="name", type=str, location="args"),
        dict(name="filter", type=str, location="args")
    )

    delete_rules = (
        dict(name="id[]", type=int, action="append", location="args"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def __calcualte_limit(self, limit, total):
        return len(total) if limit == 'All' else limit

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        total, reports = get(project_id, args, UIReport)

        res = []

        for report in reports:
            results = UIResult.query.filter_by(report_uid=report.uid).all()

            totals = list(map(lambda x: x.total, results))

            try:
                avg_page_load = sum(totals) / len(totals)
            except ZeroDivisionError:
                avg_page_load = 0

            try:
                thresholds_missed = round(report.thresholds_failed / report.thresholds_total * 100, 2)
            except ZeroDivisionError:
                thresholds_missed = 0

            data = dict(id=report.id, project_id=project_id, name=report.name, environment=report.environment,
                        browser=report.browser,
                        browser_version=report.browser_version, resolution="1380x749", url=report.base_url,
                        end_time=report.stop_time, start_time=report.start_time, duration=report.duration,
                        failures=thresholds_missed, total=10,
                        thresholds_missed=thresholds_missed,
                        avg_page_load=round(avg_page_load / 1000, 2),
                        avg_step_duration=0.5, build_id=str(uuid4()), release_id=1)

            res.append(data)

        for each in res:
            each["start_time"] = each["start_time"].replace("T", " ").replace("Z", "")
        return {"total": total, "rows": res}

    def delete(self, project_id: int):
        args = self._parser_delete.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        query_result = UIReport.query.filter(
            and_(UIReport.project_id == project.id, UIReport.id.in_(args["id[]"]))
        ).all()

        for each in query_result:
            self.__delete_report_results(project_id, each.uid)
            each.delete()
        return {"message": "deleted"}

    def __delete_report_results(self, project_id, report_id):
        results = UIResult.query.filter_by(project_id=project_id, report_uid=report_id).all()
        for result in results:
            result.delete()


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
        results = UIResult.query.filter_by(project_id=project_id, report_uid=report.uid).order_by(UIResult.id).all()

        nodes = _action_mapping["chart"]["nodes"]
        edges = _action_mapping["chart"]["edges"]

        graph_aggregation = {}
        for result in results:
            if result.name in graph_aggregation.keys():
                graph_aggregation[result.identifier].append(result)
            else:
                graph_aggregation[result.identifier] = [result]

        for name, values in graph_aggregation.items():
            aggregated_total = get_aggregated_data(report.aggregation, values)
            result = closest(values, aggregated_total)

            source_node_id = nodes[-1]["data"]["id"]
            target_node_id = str(uuid4())

            thresholds_failed = sum([d.thresholds_failed for d in values])

            status = "passed"
            if thresholds_failed > 0:
                status = "failed"

            nodes.append({
                "data": {
                    "id": target_node_id,
                    "name": name,
                    "type": values[0].type,
                    "status": status,
                    "file": f"/api/v1/artifacts/{project_id}/reports/{result.file_name}"
                }
            })

            edges.append({
                "data": {
                    "source": source_node_id,
                    "target": target_node_id,
                    "time": f"{round(aggregated_total / 1000, 2)} sec"
                },
                "classes": status
            })

        if report.loops > 1:
            source_node_id = nodes[-1]["data"]["id"]
            target_node_id = nodes[0]["data"]["id"]

            edges.append({
                "data": {"source": source_node_id, "target": target_node_id,
                         "time": "0 sec"}
            })

        table = []
        for result in results:
            data = {
                "id": result.id,
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
