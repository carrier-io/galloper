import operator
from json import loads
from typing import Optional

from flask_restful import Resource
from sqlalchemy import or_, and_

from galloper.database.models.api_reports import APIReport
from galloper.database.models.project import Project
from galloper.constants import str_to_timestamp
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
        res = [dict(id=1, project_id=project_id, name="HelloWorldChrome", environment="dev", browser="chrome",
                    browser_version="12.2.3", resolution="1380x749", url="https://www.google.com",
                    end_time="2020-04-15T08:11:37Z", start_time="2020-04-15T07:31:37Z", duration=2400,
                    failures=1, total=10, thresholds_missed=15, avg_page_load=1.4,
                    avg_step_duration=0.5, build_id=str(uuid4()), release_id=1),
               dict(id=2, project_id=project_id, name="HelloWorldFirefox", environment="dev", browser="firefox",
                    browser_version="12.2.3", resolution="1380x749", url="https://www.google.com",
                    end_time="2020-04-15T08:11:37Z", start_time="2020-04-15T07:11:37Z", duration=3600,
                    failures=1, total=10, thresholds_missed=15, avg_page_load=1.4,
                    avg_step_duration=0, build_id=str(uuid4()), release_id=1)
               ]
        for each in res:
            each["start_time"] = each["start_time"].replace("T", " ").replace("Z", "")
        return {"total": 2, "rows": res}


class VisualResultAPI(Resource):
    _action_mapping = {
        "table": [
            {
                "name": "Google",
                "speed_index": 666,
                "total_time": 2450,
                "first_bite": 354,
                "first_paint": 1345,
                "content_load": 2000,
                "dom_processing": 2130,
                "missed_thresholds": 10,
                "report": "/api/v1/artifacts/1/reports/Google_1587031762.html",
                "actions": [{
                        "action": "click",
                        "locator": "id=1",
                        "value": ""
                    },
                    {
                        "action": "type",
                        "locator": "id=1",
                        "value": "This is sparta"
                    },
                    {
                        "action": "SendKeys",
                        "locator": "id=1",
                        "value": "ENTER"
                    }
                ]
            },
            {
                "name": "Youtube",
                "speed_index": 666,
                "total_time": 2450,
                "first_bite": 354,
                "first_paint": 1345,
                "content_load": 2000,
                "dom_processing": 2130,
                "missed_thresholds": 10,
                "report": "/api/v1/artifacts/1/reports/Heston%20-%20YouTube_1587031888.html",
                "actions": [
                    {
                        "action": "click",
                        "locator": "id=1",
                        "value": ""
                    },
                    {
                        "action": "type",
                        "locator": "id=1",
                        "value": "This is sparta"
                    },
                    {
                        "action": "SendKeys",
                        "locator": "id=1",
                        "value": "ENTER"
                    }
                ]
            },
            {
                "name": "Yahoo",
                "speed_index": 666,
                "total_time": 2450,
                "first_bite": 354,
                "first_paint": 1345,
                "content_load": 2000,
                "dom_processing": 2130,
                "missed_thresholds": 10,
                "report": "/api/v1/artifacts/1/reports/Yahoo_1587031938.html",
                "actions": [
                    {
                        "action": "click",
                        "locator": "id=1",
                        "value": ""
                    },
                    {
                        "action": "type",
                        "locator": "id=1",
                        "value": "This is sparta"
                    },
                    {
                        "action": "SendKeys",
                        "locator": "id=1",
                        "value": "ENTER"
                    }
                ]
            },
            {
                "name": "Very long and nasty name in a way it is liked by our performance analysts",
                "speed_index": 666,
                "total_time": 2450,
                "first_bite": 354,
                "first_paint": 1345,
                "content_load": 2000,
                "dom_processing": 2130,
                "missed_thresholds": 10,
                "report": "/api/v1/artifacts/1/reports/EPAM%20%7C%20Enterprise%20Software%20Development%2C%20Design%20%26%20Consulting_1587031984.html",
                "actions": [
                    {
                        "action": "click",
                        "locator": "id=1",
                        "value": ""
                    },
                    {
                        "action": "type",
                        "locator": "id=1",
                        "value": "This is sparta"
                    },
                    {
                        "action": "SendKeys",
                        "locator": "id=1",
                        "value": "ENTER"
                    }
                ]
            }
        ],
        "chart": {
            "nodes": [
                { "data": { "id": 'j', "name": 'Google', "bucket": "reports", "file": "Yahoo_1587031938.html"} },
                { "data": { "id": 'e', "name": 'Youtube', "bucket": "reports", "file": "Yahoo_1587031938.html" } },
                { "data": { "id": 'k', "name": 'Yahoo', "bucket": "reports", "file": "Yahoo_1587031938.html" } },
                { "data": { "id": 'g', "name": 'Veryglongandnastynameinawayitisliked by our performance analysts', "bucket": "reports", "file": "Yahoo_1587031938.html" } }
            ],
            "edges": [
                { "data": { "source": 'j', "target": 'e', "time": 0.5} },
                { "data": { "source": 'j', "target": 'k', "time": 0.8 } },
                { "data": { "source": 'j', "target": 'g', "time": 1.2 } },
                { "data": { "source": 'e', "target": 'j', "time": 1 } },
                { "data": { "source": 'e', "target": 'k', "time": 2.4 } },
                { "data": { "source": 'k', "target": 'j', "time": 0.6 } },
                { "data": { "source": 'k', "target": 'e', "time": 0.1 } },
                { "data": { "source": 'k', "target": 'g', "time": 1.3 } },
                { "data": { "source": 'g', "target": 'j', "time": 0.7 } }
            ]
        }
    }

    def get(self, project_id: int, report_id: int, action: Optional[str] = "table"):
        return self._action_mapping[action]

