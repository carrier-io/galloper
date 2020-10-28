from sqlalchemy import Column, Integer, String, JSON, ARRAY

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base


class APIBaseline(AbstractBaseMixin, Base):
    __tablename__ = "api_baseline"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    report_id = Column(Integer, unique=False, nullable=False)
    test = Column(String, unique=False, nullable=False)
    environment = Column(String, unique=False, nullable=False)
    summary = Column(ARRAY(JSON), unique=False, nullable=False)
