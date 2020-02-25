from galloper.models import db, BaseModel


class SecurityDetails(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    detail_hash = db.Column(db.String(80), unique=False)
    details = db.Column(db.Text, unique=False)

    def to_json(self):
        return dict(id=self.id, detail_hash=self.detail_hash, details=self.details)
