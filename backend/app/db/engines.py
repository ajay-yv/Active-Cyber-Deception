from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.settings import get_database_settings


def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA cache_size=-64000;")
    cursor.execute("PRAGMA temp_store=MEMORY;")
    cursor.close()


@lru_cache(maxsize=1)
def get_real_engine():
    settings = get_database_settings()
    engine = create_engine(settings.real_database_url, future=True, connect_args={"check_same_thread": False} if settings.real_database_url.startswith("sqlite") else {})
    if settings.real_database_url.startswith("sqlite"):
        event.listen(engine, "connect", _set_sqlite_pragma)
    return engine


@lru_cache(maxsize=1)
def get_synthetic_engine():
    settings = get_database_settings()
    engine = create_engine(settings.synthetic_database_url, future=True, connect_args={"check_same_thread": False} if settings.synthetic_database_url.startswith("sqlite") else {})
    if settings.synthetic_database_url.startswith("sqlite"):
        event.listen(engine, "connect", _set_sqlite_pragma)
    return engine


@lru_cache(maxsize=1)
def get_security_engine():
    settings = get_database_settings()
    engine = create_engine(settings.security_database_url, future=True, connect_args={"check_same_thread": False} if settings.security_database_url.startswith("sqlite") else {})
    if settings.security_database_url.startswith("sqlite"):
        event.listen(engine, "connect", _set_sqlite_pragma)
    return engine


RealSessionLocal = sessionmaker(bind=get_real_engine(), autoflush=False, autocommit=False, future=True)
SyntheticSessionLocal = sessionmaker(bind=get_synthetic_engine(), autoflush=False, autocommit=False, future=True)
SecuritySessionLocal = sessionmaker(bind=get_security_engine(), autoflush=False, autocommit=False, future=True)

