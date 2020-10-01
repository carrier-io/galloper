#     Copyright 2020 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import hashlib
from datetime import datetime
from json import loads
import operator

from flask import request, current_app
from flask_restful import Resource
from sqlalchemy import or_, and_

from galloper.database.models.project import Project
from galloper.database.models.security_details import SecurityDetails
from galloper.database.models.security_reports import SecurityReport
from galloper.database.models.security_results import SecurityResults
from galloper.database.models.statistic import Statistic
from galloper.database.models.project_quota import ProjectQuota
from galloper.utils.api_utils import build_req_parser


class SecurityReportAPI(Resource):
    get_rules = (
        dict(name="offset", type=int, default=0, location="args"),
        dict(name="limit", type=int, default=0, location="args"),
        dict(name="search", type=str, default="", location="args"),
        dict(name="sort", type=str, default="", location="args"),
        dict(name="order", type=str, default="", location="args"),
        dict(name="type", type=str, default="sast", location="args"),
    )
    delete_rules = (
        dict(name="id[]", type=int, action="append", location="args"),
    )
    post_rules = (
        dict(name="project_name", type=str, location="json"),
        dict(name="app_name", type=str, location="json"),
        dict(name="scan_time", type=float, location="json"),
        dict(name="dast_target", type=str, location="json"),
        dict(name="sast_code", type=str, location="json"),
        dict(name="scan_type", type=str, location="json"),
        dict(name="findings", type=int, location="json"),
        dict(name="false_positives", type=int, location="json"),
        dict(name="excluded", type=int, location="json"),
        dict(name="info_findings", type=int, location="json"),
        dict(name="environment", type=str, location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_post = build_req_parser(rules=self.post_rules)
        self._parser_delete = build_req_parser(rules=self.delete_rules)

    def get(self, project_id):
        reports = []
        args = self._parser_get.parse_args(strict=False)
        search_ = args.get("search")
        limit_ = args.get("limit")
        offset_ = args.get("offset")
        scan_type = args.get("type").upper()
        if args.get("sort"):
            sort_rule = getattr(getattr(SecurityResults, args["sort"]), args["order"])()
        else:
            sort_rule = SecurityResults.id.desc()
        if not args.get("search") and not args.get("sort"):
            total = SecurityResults.query.filter(and_(SecurityResults.project_id == project_id,
                                                      SecurityResults.scan_type == scan_type)
                                                 ).order_by(sort_rule).count()
            res = SecurityResults.query.filter(and_(SecurityResults.project_id == project_id,
                                                    SecurityResults.scan_type == scan_type)).\
                order_by(sort_rule).limit(limit_).offset(offset_).all()
        else:
            filter_ = and_(SecurityResults.project_id == project_id, SecurityResults.scan_type == scan_type,
                      or_(SecurityResults.project_name.like(f"%{search_}%"),
                          SecurityResults.app_name.like(f"%{search_}%"),
                          SecurityResults.scan_type.like(f"%{search_}%"),
                          SecurityResults.environment.like(f"%{search_}%")))
            res = SecurityResults.query.filter(filter_).order_by(sort_rule).limit(limit_).offset(offset_).all()
            total = SecurityResults.query.filter(filter_).order_by(sort_rule).count()
        for each in res:
            each_json = each.to_json()
            each_json["scan_time"] = each_json["scan_time"].replace("T", " ").split(".")[0]
            each_json["scan_duration"] = float(each_json["scan_duration"])
            reports.append(each_json)
        return {"total": total, "rows": reports}

    def delete(self, project_id: int):
        args = self._parser_delete.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        for each in SecurityReport.query.filter(
            and_(SecurityReport.project_id == project.id, SecurityReport.report_id.in_(args["id[]"]))
        ).order_by(SecurityReport.id.asc()).all():
            each.delete()
        for each in SecurityResults.query.filter(
            SecurityResults.id.in_(args["id[]"])
        ).order_by(SecurityResults.id.asc()).all():
            each.delete()
        return {"message": "deleted"}

    def post(self, project_id: int):
        args = self._parser_post.parse_args(strict=False)
        project = Project.get_or_404(project_id)
        # TODO move sast/dast quota checks to a new endpoint, which will be triggered before the scan
        if args["scan_type"].lower() == 'sast':
            if not ProjectQuota.check_quota(project_id=project_id, quota='sast_scans'):
                return {"Forbidden": "The number of sast scans allowed in the project has been exceeded"}
        elif args["scan_type"].lower() == 'dast':
            if not ProjectQuota.check_quota(project_id=project_id, quota='dast_scans'):
                return {"Forbidden": "The number of dast scans allowed in the project has been exceeded"}
        report = SecurityResults(scan_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                 project_id=project.id,
                                 scan_duration=args["scan_time"],
                                 project_name=args["project_name"],
                                 app_name=args["app_name"],
                                 dast_target=args["dast_target"],
                                 sast_code=args["sast_code"],
                                 scan_type=args["scan_type"],
                                 findings=args["findings"]-(args["false_positives"]+args["excluded"]),
                                 false_positives=args["false_positives"],
                                 excluded=args["excluded"],
                                 info_findings=args["info_findings"],
                                 environment=args["environment"])
        report.insert()

        statistic = Statistic.query.filter_by(project_id=project_id).first()
        if args["scan_type"].lower() == 'sast':
            setattr(statistic, 'sast_scans', Statistic.sast_scans + 1)
        elif args["scan_type"].lower() == 'dast':
            setattr(statistic, 'dast_scans', Statistic.dast_scans + 1)
        statistic.commit()

        return {"id": report.id}


class FindingsAPI(Resource):
    get_rules = (
        dict(name="id", type=int, location="args"),
        dict(name="type", type=str, location="args"),
        dict(name="filter", type=str, default="", location="args")
    )
    put_rules = (
        dict(name="id", type=int, location="json"),
        dict(name="action", type=str, location="json"),
        dict(name="issue_id", type=int, default=None, location="json"),
        dict(name="issues_id", type=list, default=[], location="json")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)
        self._parser_put = build_req_parser(rules=self.put_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        filter_ = []
        filter_.append(SecurityReport.project_id == project_id)
        filter_.append(SecurityReport.report_id == args["id"])
        if args["type"] == "false_positives":
            filter_.append(SecurityReport.false_positive == 1)
        elif args["type"] == "findings":
            filter_.append(SecurityReport.info_finding == 0)
            filter_.append(SecurityReport.false_positive == 0)
            filter_.append(SecurityReport.excluded_finding == 0)
        elif args["type"] == "info_findings":
            filter_.append(SecurityReport.info_finding == 1)
        elif args["type"] == "excluded_finding":
            filter_.append(SecurityReport.excluded_finding == 1)
        if args.get("filter"):
            for key, value in loads(args.get("filter")).items():
                filter_.append(getattr(SecurityReport, key).like(f"%{value}%"))
        filter_ = and_(*tuple(filter_))
        issues = SecurityReport.query.filter(filter_).all()
        results = []
        for issue in issues:
            _res = issue.to_json()
            _res["details"] = SecurityDetails.query.filter_by(id=_res["details"]).first().details
            results.append(_res)
        return results

    def post(self, project_id: int):
        finding_db = None
        for finding in request.json:
            md5 = hashlib.md5(finding["details"].encode("utf-8")).hexdigest()
            hash_id = SecurityDetails.query.filter(
                and_(SecurityDetails.project_id == project_id, SecurityDetails.detail_hash == md5)
            ).first()
            if not hash_id:
                hash_id = SecurityDetails(detail_hash=md5, project_id=project_id, details=finding["details"])
                hash_id.insert()
            # Verify issue is false_positive or ignored
            finding["details"] = hash_id.id
            finding['project_id'] = project_id
            entrypoints = ""
            if finding.get("endpoints"):
                for each in finding.get("endpoints"):
                    if isinstance(each, list):
                        entrypoints += "<br />".join(each)
                    else:
                        entrypoints += f"<br />{each}"
            finding["endpoints"] = entrypoints
            issue = SecurityReport.query.filter(and_(
                SecurityReport.project_id == project_id,
                SecurityReport.issue_hash == finding['issue_hash'])).first()
            if issue:
                finding['severity'] = issue.severity
            if not (finding["false_positive"] == 1 or finding["excluded_finding"] == 1):
                # TODO: add validation that finding is a part of project, application. etc.
                issues = SecurityReport.query.filter(
                    and_(SecurityReport.project_id == project_id,
                         SecurityReport.issue_hash == finding["issue_hash"],
                         or_(SecurityReport.false_positive == 1,
                             SecurityReport.excluded_finding == 1)
                         )).all()
                false_positive = sum(issue.false_positive for issue in issues)
                excluded_finding = sum(issue.excluded_finding for issue in issues)
                finding["false_positive"] = 1 if false_positive > 0 else 0
                finding["excluded_finding"] = 1 if excluded_finding > 0 else 0
            finding_db = SecurityReport(**finding)
            finding_db.add()
        if finding_db:
            finding_db.commit()

    def put(self, project_id: int):
        # TODO: this thing need to be reworked, as it will be slow as hell
        args = self._parser_put.parse_args(strict=False)
        issues_id = []
        if args["issue_id"]:
            issues_id.append(args["issue_id"])
        else:
            issues_id = args["issues_id"]
        if args["action"] in ("false_positive", "excluded_finding"):
            upd = {args["action"]: 1}
        elif args["action"] == 'valid':
            upd = {"false_positive": 0, "excluded_finding": 0}
        elif args["action"] in ("Critical", "High", "Medium", "Low", "Info"):
            upd = {'severity': args["action"]}
        else:
            return {"message": "Action is invalid"}, 400

        for issue_id in issues_id:
            issue_hash = SecurityReport.query.filter(and_(SecurityReport.project_id == project_id,
                                                          SecurityReport.id == issue_id)
                                                     ).first().issue_hash
            SecurityReport.query.filter(and_(
                SecurityReport.project_id == project_id,
                SecurityReport.issue_hash == issue_hash)
            ).update(upd)
            SecurityReport.commit()
            if args["action"] in ("false_positive", "excluded_finding", "valid"):
                reports = SecurityReport.query.filter(and_(
                    SecurityReport.project_id == project_id,
                    SecurityReport.issue_hash == issue_hash)
                ).with_entities(SecurityReport.report_id).distinct()
                for report in reports:
                    false_positive = SecurityReport.query.filter(and_(
                        SecurityReport.report_id == report.report_id,
                        SecurityReport.false_positive == 1)
                    ).count()
                    ignored = SecurityReport.query.filter(and_(
                        SecurityReport.report_id == report.report_id,
                        SecurityReport.excluded_finding == 1)
                    ).count()
                    findings = SecurityReport.query.filter(and_(
                        SecurityReport.report_id == report.report_id)
                    ).count()
                    SecurityResults.query.filter(
                        SecurityResults.id == report.report_id
                    ).update({"false_positives": false_positive, "excluded": ignored,
                              "findings": findings-(false_positive+ignored)})
                    SecurityResults.commit()
        return {"message": "accepted"}


class FindingsAnalysisAPI(Resource):
    get_rules = (
        dict(name="project_name", type=str, location="args"),
        dict(name="app_name", type=str, location="args"),
        dict(name="scan_type", type=str, location="args"),
        dict(name="type", type=str, default="false-positive", location="args")
    )

    def __init__(self):
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_get = build_req_parser(rules=self.get_rules)

    def get(self, project_id: int):
        args = self._parser_get.parse_args(strict=False)
        projects_filter = and_(SecurityResults.project_id == project_id,
                               SecurityResults.project_name == args["project_name"],
                               SecurityResults.app_name == args["app_name"],
                               SecurityResults.scan_type == args["scan_type"])
        ids = SecurityResults.query.filter(projects_filter).all()
        ids = [each.id for each in ids]
        hashes = SecurityReport.query.filter(
            and_(SecurityReport.false_positive == 1, SecurityReport.report_id.in_(ids))
            ).with_entities(SecurityReport.issue_hash).distinct()
        return [_.issue_hash for _ in hashes]
