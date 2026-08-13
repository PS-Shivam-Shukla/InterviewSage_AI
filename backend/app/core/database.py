"""
Database engine, session factory, and dependency provider.
Configured with production-ready connection pooling and SQLite compatibility (Audit H-5).
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings


def _set_sqlite_pragmas(dbapi_conn, _connection_record):
    """Enable WAL mode and foreign key enforcement for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def build_engine(database_url: str | None = None):
    """
    Build SQLAlchemy engine with production-ready connection pool settings.
    """
    url = database_url or settings.database_url
    is_sqlite = url.startswith("sqlite")

    if is_sqlite:
        connect_args = {"check_same_thread": False}
        engine = create_engine(
            url,
            connect_args=connect_args,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        event.listen(engine, "connect", _set_sqlite_pragmas)
    else:
        # Production PostgreSQL connection pool settings
        engine = create_engine(
            url,
            echo=settings.debug,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=30,
        )

    return engine


engine = build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
