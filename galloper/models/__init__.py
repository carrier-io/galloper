from json import dumps
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class BaseModel(object):
    def __repr__(self):
        return dumps(self.to_json(), indent=2)

    def to_json(self):
        raise NotImplemented()

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def commit():
        db.session.commit()
