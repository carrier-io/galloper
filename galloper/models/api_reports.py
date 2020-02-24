from galloper.models import db, BaseModel


class APIReport(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False)
    environment = db.Column(db.String(80), unique=False)
    type = db.Column(db.String(80), unique=False)
    end_time = db.Column(db.String(80), unique=False)
    start_time = db.Column(db.String(80), unique=False)
    failures = db.Column(db.Integer, unique=False)
    total = db.Column(db.Integer, unique=False)
    thresholds_missed = db.Column(db.Integer, unique=False, nullable=True)
    throughput = db.Column(db.Float, unique=False)
    vusers = db.Column(db.Integer, unique=False)
    pct95 = db.Column(db.Float, unique=False)
    duration = db.Column(db.Integer, unique=False)
    build_id = db.Column(db.String(80), unique=True)
    lg_type = db.Column(db.String(12), unique=False)
    onexx = db.Column(db.Integer, unique=False)
    twoxx = db.Column(db.Integer, unique=False)
    threexx = db.Column(db.Integer, unique=False)
    fourxx = db.Column(db.Integer, unique=False)
    fivexx = db.Column(db.Integer, unique=False)
    requests = db.Column(db.Text, unique=False)

    def to_json(self):
        return {
            "id": self.id,
            "start_time": self.start_time,
            "name": self.name,
            "environment": self.environment,
            "type": self.type,
            "end_time": self.end_time,
            "failures": self.failures,
            "total": self.total,
            "thresholds_missed": self.thresholds_missed,
            "throughput": self.throughput,
            "vusers": self.vusers,
            "pct95": self.pct95,
            "duration": self.duration,
            "lg_type": self.lg_type,
            "build_id": self.build_id,
            "1xx": self.onexx,
            "2xx": self.twoxx,
            "3xx": self.threexx,
            "4xx": self.fourxx,
            "5xx": self.fivexx,
            "requests": self.requests.split(";")
        }
