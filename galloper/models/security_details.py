from galloper.models import db, BaseModel


class SecurityDetails(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    detail_hash = db.Column(db.String(80), unique=False)
    details = db.Column(db.Text, unique=False)
