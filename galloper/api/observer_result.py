from flask_restful import Resource

from galloper.database.models.ui_result import UIResult
from galloper.utils.api_utils import build_req_parser


class UIResultsAPI(Resource):
    post_rules = (
        dict(name="metrics", type=dict, location="json"),
        dict(name="bucket_name", type=str, location="json"),
        dict(name="thresholds_total", type=int, location="json"),
        dict(name="thresholds_failed", type=int, location="json"),
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_post = build_req_parser(rules=self.post_rules)
        # self._parser_put = build_req_parser(rules=self.put_rules)

    def post(self, project_id: int, report_id: int):
        # html
        # save to minio

        args = self._parser_post.parse_args()

        metrics = args["metrics"]

        result = UIResult(
            project_id=project_id,
            report_id=report_id,
            bucket_name=args["bucket_name"],
            thresholds_total=args["thresholds_total"],
            thresholds_failed=args["thresholds_failed"],
            requests=metrics["requests"],
            domains=metrics["domains"],
            total=metrics["total"],
            speed_index=metrics["speed_index"],
            time_to_first_byte=metrics["time_to_first_byte"],
            time_to_first_paint=metrics["time_to_first_paint"],
            dom_content_loading=metrics["dom_content_loading"],
            dom_processing=metrics["dom_processing"]
        )

        result.insert()

        return result.to_json()
