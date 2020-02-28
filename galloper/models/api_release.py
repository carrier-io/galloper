from galloper.models import db, AbstractBaseModel


class APIRelease(AbstractBaseModel):
    id = db.Column(db.Integer, primary_key=True)
    release_date = db.Column(db.String(80), unique=False)
    release_name = db.Column(db.String(80), unique=False)
