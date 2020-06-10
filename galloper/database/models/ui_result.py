from sqlalchemy import Column, Integer, String, JSON

from galloper.database.abstract_base import AbstractBaseMixin
from galloper.database.db_manager import Base


class UIResult(AbstractBaseMixin, Base):
    __tablename__ = "ui_result"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    report_id = Column(Integer, unique=False, nullable=False)
    name = Column(String(128), unique=False)
    type = Column(String(128), unique=False)
    bucket_name = Column(String(128), unique=False)
    file_name = Column(String(128), unique=False)
    thresholds_total = Column(Integer, unique=False)
    thresholds_failed = Column(Integer, unique=False)
    requests = Column(Integer, unique=False)
    domains = Column(Integer, unique=False)
    total = Column(Integer, unique=False)
    speed_index = Column(Integer, unique=False)
    time_to_first_byte = Column(Integer, unique=False)
    time_to_first_paint = Column(Integer, unique=False)
    dom_content_loading = Column(Integer, unique=False)
    dom_processing = Column(Integer, unique=False)
    locators = Column(JSON, unique=False, default=[{}])
    resolution = Column(String(128), unique=False)
    browser_version = Column(String(128), unique=False, nullable=True)
