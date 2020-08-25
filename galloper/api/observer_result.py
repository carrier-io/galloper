from flask_restful import Resource

from galloper.database.models.ui_result import UIResult
from galloper.utils.api_utils import build_req_parser


class UIResultsAPI(Resource):
    post_rules = (
        dict(name="metrics", type=dict, location="json"),
        dict(name="bucket_name", type=str, location="json"),
        dict(name="file_name", type=str, location="json"),
        dict(name="thresholds_total", type=int, location="json"),
        dict(name="thresholds_failed", type=int, location="json"),
        dict(name="locators", default=[], type=list, location="json"),
        dict(name="resolution", type=str, location="json"),
        dict(name="browser_version", type=str, location="json"),
        dict(name="name", type=str, location="json"),
        dict(name="identifier", type=str, location="json"),
        dict(name="type", type=str, location="json"),
    )

    put_rules = (
        dict(name="locators", default=[], type=list, location="json"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_put = build_req_parser(rules=self.put_rules)

    def post(self, project_id: int, report_id: str):
        args = self._parser_post.parse_args()

        metrics = args["metrics"]

        result = UIResult(
            project_id=project_id,
            report_uid=report_id,
            name=args["name"],
            identifier=args['identifier'],
            type=args["type"],
            bucket_name=args["bucket_name"],
            file_name=args["file_name"],
            thresholds_total=args["thresholds_total"],
            thresholds_failed=args["thresholds_failed"],
            requests=metrics["requests"],
            domains=metrics["domains"],
            total=metrics["total"],
            speed_index=metrics["speed_index"],
            time_to_first_byte=metrics["time_to_first_byte"],
            time_to_first_paint=metrics["time_to_first_paint"],
            dom_content_loading=metrics["dom_content_loading"],
            dom_processing=metrics["dom_processing"],
            locators=args["locators"],
            resolution=args["resolution"],
            browser_version=args["browser_version"]
        )

        result.insert()
        return result.to_json()

    def put(self, project_id: int, report_id: int):
        args = self._parser_put.parse_args()
        results = UIResult.query.filter_by(project_id=project_id, id=report_id).first_or_404()
        results.locators = args["locators"]

        results.commit()

        return results.to_json()
