from galloper.models import db, AbstractBaseModel


class APIReport(AbstractBaseModel):
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
    release_id = db.Column(db.Integer, nullable=True)

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        json_dict = super().to_json(exclude_fields=("requests",))
        json_dict["requests"] = self.requests.split(";")
        return json_dict
