import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .logging import setup_logging
from app.database.connection import engine


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    """
    # Startup
    logger.info("Starting up HRMS FastAPI application...")
    
    # Setup logging
    setup_logging()
    logger.info("Logging configured")
    
    # Create database tables
    try:
        from app.database.base import Base
        # Simple synchronous create_all
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down HRMS FastAPI application...")
    
    # Cleanup
    engine.dispose()
    logger.info("Database engine disposed")
