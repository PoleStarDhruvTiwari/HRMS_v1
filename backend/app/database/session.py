import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import engine


logger = logging.getLogger(__name__)


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)



def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Handles session lifecycle and errors.
    """
    db = SessionLocal()
    try:
        logger.debug("Database session started")
        yield db
        db.commit()
        logger.debug("Database session committed")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error, rolling back: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error, rolling back: {str(e)}")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


def get_db_session() -> Session:
    """Get database session without context manager."""
    return SessionLocal()