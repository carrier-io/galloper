from json import dumps
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AbstractBaseModel(db.Model):
    __abstract__ = True

    def __repr__(self) -> str:
        return dumps(self.to_json(), indent=2)

    def to_json(self, exclude_fields: tuple = ()) -> dict:
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns if column not in exclude_fields
        }

    def add(self) -> None:
        db.session.add(self)

    def insert(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete(self) -> None:
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def commit() -> None:
        db.session.commit()
