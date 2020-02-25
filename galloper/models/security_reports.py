from galloper.models import db, BaseModel


class SecurityReport(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, nullable=False)
    issue_hash = db.Column(db.String(80), unique=False)
    tool_name = db.Column(db.String(80), unique=False)
    description = db.Column(db.String(80), unique=False)
    severity = db.Column(db.String(10), unique=False)
    details = db.Column(db.Integer, unique=False)
    endpoints = db.Column(db.Text, unique=False)
    false_positive = db.Column(db.Integer, unique=False)
    info_finding = db.Column(db.Integer, unique=False)
    excluded_finding = db.Column(db.Integer, unique=False)

    def to_json(self):
        return dict(id=self.id, report_id=self.report_id,
                    issue_hash=self.issue_hash, tool_name=self.tool_name,
                    description=self.description, severity=self.severity,
                    details=self.details, endpoints=self.endpoints,
                    false_positive=self.false_positive, info_finding=self.info_finding,
                    excluded_finding=self.excluded_finding)
