"""
PostgreSQL session layer for future / current DB integration.

When DATABASE_URL is unset, get_db() yields None and SQL tools return a
user-friendly unavailable message instead of crashing the API.
"""

from contextlib import contextmanager
from typing import Generator, Optional

from backend.core.logging import get_logger
from backend.core.settings import get_settings

logger = get_logger(__name__)

_engine = None
_SessionLocal = None


def _init_engine():
    global _engine, _SessionLocal

    if _engine is not None:
        return

    settings = get_settings()
    if not settings.database_url:
        logger.info("DATABASE_URL not configured — SQL execution disabled")
        return

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
    except ImportError as exc:
        logger.error("SQLAlchemy is required for database access: %s", exc)
        return

    _engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )
    _SessionLocal = sessionmaker(
        bind=_engine,
        autocommit=False,
        autoflush=False,
        future=True,
    )
    logger.info("PostgreSQL engine initialized")


def get_engine():
    _init_engine()
    return _engine


@contextmanager
def session_scope() -> Generator[Optional[object], None, None]:
    """Context manager yielding a SQLAlchemy session or None."""
    _init_engine()
    if _SessionLocal is None:
        yield None
        return

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Optional[object], None, None]:
    """FastAPI dependency for DB sessions."""
    with session_scope() as session:
        yield session
