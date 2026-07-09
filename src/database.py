"""SQLAlchemy database connection for SIP-Edge."""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

engine = None
SessionLocal = None


def init_db(database_url: str = None) -> None:
    global engine, SessionLocal
    if database_url is None:
        host = os.environ["DB_HOST"]
        port = os.environ["DB_PORT"]
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        name = os.environ["DB_NAME"]
        database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
    logger.info("Initializing database connection")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
