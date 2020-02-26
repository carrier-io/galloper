from galloper.models import db, BaseModel


class APIRelease(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    release_date = db.Column(db.String(80), unique=False)
    release_name = db.Column(db.String(80), unique=False)

    def to_json(self):
        return dict(id=self.id, release_date=self.release_date, release_name=self.release_name)

