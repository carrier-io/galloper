from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base
from sqlalchemy import String, Column, Integer, Float, Text, Boolean


class UIReport(AbstractBaseMixin, Base):
    __tablename__ = "ui_report"

    id = Column(Integer, primary_key=True)
    test_name = Column(String(128), unique=False)
    project_id = Column(Integer, unique=False, nullable=False)
    start_time = Column(String(128), unique=False)
    stop_time = Column(String(128), unique=False)
    is_active = Column(Boolean, unique=False)
