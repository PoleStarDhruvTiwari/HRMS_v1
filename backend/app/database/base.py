import logging
from sqlalchemy.orm import declarative_base


logger = logging.getLogger(__name__)


Base = declarative_base()


def init_models():
    """Initialize all database models."""
    from app.apis.auth import models as auth_models
    from app.apis.users import models as user_models
    from app.apis.employee_availability import models as employee_availability_models
    from app.apis.hierarchy.employee_hierarchy import models as employee_hierarchy_models
    from app.apis.organization.designations import models as designation_models
    from app.apis.organization.offices import models as office_models
    from app.apis.organization.shifts import models as shift_models
    from app.apis.organization.teams import models as team_models
    from app.apis.access_control.roles import models as role_models
    from app.apis.access_control.permissions import models as permission_models
    from app.apis.access_control.role_permissions import models as role_permission_models
    from app.apis.access_control.user_permissions import models as user_permission_models
    from app.apis.access_control.modules import models as module_models



    logger.info("Database models initialized")