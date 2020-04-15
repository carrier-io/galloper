from sqlalchemy import Column, Integer, String

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base


class UIResult(AbstractBaseMixin, Base):
    __tablename__ = "ui_result"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    report_id = Column(Integer, unique=False, nullable=False)
    command = Column(String(128), unique=False)
    target = Column(String(128), unique=False)
    value = Column(String(128), unique=False)
