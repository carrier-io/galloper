import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_conn = {}

def get_connection():
    global _conn
    pid = os.getpid()
    if _conn and _conn.get(pid):
        return _conn[pid]
    _conn[pid] = sessionmaker(bind=create_engine("sqlite:////tmp/test.db", pool_pre_ping=True))()
    return _conn[pid]

