import logging
from sqlalchemy.orm import declarative_base


logger = logging.getLogger(__name__)


Base = declarative_base()


def init_models():
    """Initialize all database models."""
    from app.apis.auth import models as auth_models
    from app.apis.users import models as user_models
    from app.apis.employee_availability import models as employee_availability_models
    
    logger.info("Database models initialized")