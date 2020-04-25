from flask_restful import Resource
from galloper.database.models.statistic import Statistic
from galloper.database.models.project_quota import ProjectQuota
from galloper.utils.api_utils import build_req_parser


class StatisticAPI(Resource):
    result_rules = (
        dict(name="ts", type=int, location="json"),
        dict(name="results", type=str, location="json"),
        dict(name="stderr", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._result_parser = build_req_parser(rules=self.result_rules)

    def get(self, project_id: int):
        statistic = Statistic.query.filter_by(project_id=project_id).first().to_json()
        quota = ProjectQuota.query.filter_by(project_id=project_id).first().to_json()
        stats = {}
        for each in ["performance_test_runs", "sast_scans", "dast_scans", "storage_space", "tasks_count",
                     "tasks_executions"]:

            stats[each] = {"current": statistic[each], "quota": quota[each]}
        return stats
