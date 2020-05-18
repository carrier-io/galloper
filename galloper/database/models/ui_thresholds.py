from sqlalchemy import Column, Integer, String, JSON

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base


class UIThresholds(AbstractBaseMixin, Base):
    __tablename__ = "ui_thresholds"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test = Column(String, unique=False, nullable=False)
    environment = Column(String, unique=False, nullable=False)
    scope = Column(String, unique=False, nullable=False)
    metric = Column(Integer, unique=False, nullable=False)
    target = Column(String, unique=False, nullable=False)
    aggregation = Column(String, unique=False, nullable=False)
    comparison = Column(String, unique=False, nullable=False)
