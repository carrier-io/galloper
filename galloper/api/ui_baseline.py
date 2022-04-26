from flask_restful import Resource
from galloper.utils.api_utils import build_req_parser
from galloper.database.models.project import Project
from galloper.database.models.ui_baseline import UIBaseline


class UIBaselineAPI(Resource):
    get_rules = (
        dict(name="test_name", type=str, location="args"),
        dict(name="env", type=str, location="args")
    )
    post_rules = (
        dict(name="test_name", type=str, location="json"),
        dict(name="report_id", type=str, location="json"),
        dict(name="env", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        baseline = UIBaseline.query.filter_by(project_id=project.id, test=args.get("test_name"),
                                              environment=args.get("env")).first()
        report_id = baseline.report_id if baseline else 0
        return {"baseline_id": report_id}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        baseline = UIBaseline.query.filter_by(project_id=project.id, test=args.get("test_name"),
                                              environment=args.get("env")).first()
        if baseline:
            baseline.delete()
        baseline = UIBaseline(test=args["test_name"],
                              environment=args["env"],
                              project_id=project.id,
                              report_id=args["report_id"])
        baseline.insert()
        return {"message": "baseline is set"}
