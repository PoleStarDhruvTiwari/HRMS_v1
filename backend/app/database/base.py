import logging
from sqlalchemy.orm import declarative_base


logger = logging.getLogger(__name__)


Base = declarative_base()


def init_models():
    """Initialize all database models."""
    from app.apis.auth import models as auth_models
    from app.apis.employees_profile import models as employee_models
    
    logger.info("Database models initialized")