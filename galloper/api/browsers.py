from flask_restful import Resource

from galloper.utils.api_utils import build_req_parser


class BrowsersAPI(Resource):

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)

    _get_rules = ()

    def get(self, project_id: int):
        return {
            "chrome": [
                "85.0",
                "84.0",
                "83.0",
            ],
            "firefox": [
                "73.0",
                "72.0"
            ]
        }
