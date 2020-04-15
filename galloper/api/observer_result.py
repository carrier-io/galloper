from flask_restful import Resource

from galloper.database.models.ui_result import UIResult
from galloper.utils.api_utils import build_req_parser


class UIResultsAPI(Resource):
    # post_rules = (
    #     dict(name="test_name", type=str, location="json"),
    #     dict(name="time", type=str, location="json")
    # )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        # self._parser_post = build_req_parser(rules=self.post_rules)
        # self._parser_put = build_req_parser(rules=self.put_rules)
        pass

    def post(self, project_id: int, report_id: int):
        args = self._parser_post.parse_args()

        result = UIResult(
            project_id=project_id,
            report_id=report_id
        )

        return result.to_json()
