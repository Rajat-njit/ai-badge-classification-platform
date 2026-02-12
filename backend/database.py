"""
SQLAlchemy engine, session factory, and table initialisation.

All other modules import get_db() for dependency injection.
create_tables() is called once from main.py lifespan handler.
"""

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.governance_log import Base

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./badges.db")

# connect_args required for SQLite to allow multi-threaded access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all tables defined in Base metadata. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a database session and guarantees cleanup.

    Usage in route:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager version for use outside of FastAPI dependency injection
    (e.g. scripts, tests).

    Usage:
        with get_db_context() as db:
            db.add(record)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
