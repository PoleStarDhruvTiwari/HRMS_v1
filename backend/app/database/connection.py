import logging
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings


logger = logging.getLogger(__name__)


# Create synchronous engine for SQLAlchemy 1.4/2.0
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.DEBUG,
    future=True
)

# For async support (if needed)
async_engine = None
if settings.DATABASE_URL.startswith("postgresql+asyncpg"):
    async_engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+asyncpg"),
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )


def test_connection():
    """Test database connection."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False