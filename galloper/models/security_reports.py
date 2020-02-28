from galloper.models import db, AbstractBaseModel


class SecurityReport(AbstractBaseModel):
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
