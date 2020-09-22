import requests
from flask_restful import Resource

from galloper.constants import GRID_ROUTER_URL
from galloper.utils.api_utils import build_req_parser


class BrowsersAPI(Resource):

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.get_parser = build_req_parser(rules=self._get_rules)

    _get_rules = ()

    def get(self, project_id: int):
        res = requests.get(GRID_ROUTER_URL)
        if res.status_code != 200:
            return {}

        result = {}
        for item in res.json():
            versions = []
            for version in item['Versions']:
                versions.append(version['Number'])
            result[item['Name']] = versions

        return result
