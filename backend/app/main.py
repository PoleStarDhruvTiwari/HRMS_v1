# import logging
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.core.events import lifespan
# from app.core.config import settings
# from app.shared.middleware import setup_middleware
# from app.shared.exceptions import setup_exception_handlers
# from app.apis.auth.routers import router as auth_router
# from app.apis.users.routers import router as users_router
# from app.apis.employee_availability.routers import router as employee_availability_router
# from app.apis.access_control.roles.routers import router as roles_router
# from app.apis.access_control.modules.routers import router as modules_router
# # In your main.py or app/__init__.py
# from app.apis.organization.offices.routers import router as offices_router

# # In your main.py or app/__init__.py
# from app.apis.organization.shifts.routers  import router as shifts_router
# # In your main.py or app/__init__.py
# from app.apis.organization.teams.routers import router as teams_router

# # In your main.py or app/__init__.py
# from app.apis.organization.designations.routers import router as designations_router











# # In your main.py or app/__init__.py



# # Initialize logger
# logger = logging.getLogger(__name__)

# # Create FastAPI application
# app = FastAPI(
#     title="HRMS FastAPI Backend",
#     description="Human Resource Management System API",
#     version="1.0.0",
#     docs_url="/api/docs" if settings.DEBUG else None,
#     redoc_url="/api/redoc" if settings.DEBUG else None,
#     openapi_url="/api/openapi.json" if settings.DEBUG else None,
#     lifespan=lifespan
# )

# # Setup CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[settings.FRONTEND_ORIGIN],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Setup middleware
# setup_middleware(app)

# # Setup exception handlers
# setup_exception_handlers(app)

# # Include routers
# app.include_router(auth_router)
# app.include_router(users_router)
# app.include_router(employee_availability_router)
# app.include_router(roles_router)
# app.include_router(modules_router)
# app.include_router(offices_router)
# app.include_router(shifts_router)
# app.include_router(teams_router)
# app.include_router(designations_router)


# @app.get("/")
# async def root():
#     """Root endpoint with API information."""
#     logger.info("Root endpoint accessed")
#     return {
#         "message": "HRMS FastAPI Backend",
#         "version": "1.0.0",
#         "docs": "/api/docs" if settings.DEBUG else None,
#         "status": "operational"
#     }


# @app.get("/api/health")
# async def health_check():
#     """Health check endpoint for monitoring."""
#     logger.debug("Health check endpoint accessed")
#     return {
#         "status": "healthy",
#         "service": "hrms-backend",
#         "version": "1.0.0"
#     }


# if __name__ == "__main__":
#     import uvicorn
    
#     logger.info(f"Starting HRMS FastAPI application on http://0.0.0.0:8001")
#     logger.info(f"Debug mode: {settings.DEBUG}")
#     logger.info(f"Log level: {settings.LOG_LEVEL}")
    
#     uvicorn.run(
#         "app.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=settings.DEBUG,
#         log_level=settings.LOG_LEVEL.lower()
#     )




# In your main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.shared.middleware import setup_middleware
from app.shared.exceptions import setup_exception_handlers
from app.apis.auth.routers import router as auth_router
from app.apis.users.routers import router as users_router
from app.apis.employee_availability.routers import router as employee_availability_router
from app.apis.access_control.roles.routers import router as roles_router
from app.apis.access_control.modules.routers import router as modules_router
from app.apis.organization.offices.routers import router as offices_router
from app.apis.organization.shifts.routers import router as shifts_router
from app.apis.organization.teams.routers import router as teams_router
from app.apis.organization.designations.routers import router as designations_router

# Import permission router
from app.apis.access_control.permissions.routes import router as permissions_router 
from app.apis.access_control.user_permissions.routes import router as user_permissions_router
# see properly i have added the word routes not router 

# Import the router
from app.apis.access_control.role_permissions.routes import router as role_permissions_router



logger = logging.getLogger(__name__)


def wait_for_database(db_url: str, max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for database to be ready."""
    logger.info("⏳ Waiting for database connection...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection established")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: Database not ready, retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"❌ Failed to connect to database after {max_retries} attempts")
                return False
    return False


def sync_permissions_on_startup() -> bool:
    """Run permission synchronization on application startup."""
    try:
        from app.core.permission_sync import sync_permissions, get_permission_sync_status
        
        logger.info("🔄 Starting permission synchronization...")
        
        # Get current status
        status = get_permission_sync_status()
        logger.info(f"📊 Pre-sync status: Code={status['code']['total']}, DB Active={status['database']['active']}")
        
        # Run sync
        result = sync_permissions()
        
        logger.info(f"✅ Permission sync completed:")
        logger.info(f"   • Inserted: {len(result['inserted'])} new permissions")
        logger.info(f"   • Reactivated: {len(result['reactivated'])} permissions")
        logger.info(f"   • Soft-deleted: {len(result['soft_deleted'])} permissions")
        
        if result['inserted']:
            logger.info("   New permissions:")
            for perm in result['inserted']:
                logger.info(f"     - {perm}")
        
        # Verify sync
        status = get_permission_sync_status()
        if status['summary']['in_sync']:
            logger.info("🎉 Code and database permissions are synchronized!")
        else:
            logger.warning("⚠️ Permission drift detected after sync")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Cannot import permission sync module: {e}")
        logger.warning("⚠️ Skipping permission sync. Make sure app.core.permission_sync exists.")
        return False
    except Exception as e:
        logger.error(f"❌ Permission sync failed: {str(e)}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Runs permission sync on startup.
    """
    logger.info("🚀 HRMS Application Starting Up...")
    
    # Wait for database
    if not wait_for_database(settings.DATABASE_URL):
        logger.error("⚠️ Starting without database connection - some features may not work")
    
    # Run permission sync
    sync_permissions_on_startup()
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("👋 HRMS Application Shutting Down...")


# Create FastAPI application
app = FastAPI(
    title="HRMS FastAPI Backend",
    description="Human Resource Management System API",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan  # ✅ Add lifespan here
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup middleware
setup_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(employee_availability_router)
app.include_router(roles_router)
app.include_router(modules_router)
app.include_router(offices_router)
app.include_router(shifts_router)
app.include_router(teams_router)
app.include_router(designations_router)
app.include_router(permissions_router)  # ✅ Add permissions router
app.include_router(user_permissions_router)  # ✅ Add user permissions router
app.include_router(role_permissions_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    logger.info("Root endpoint accessed")
    return {
        "message": "HRMS FastAPI Backend",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.DEBUG else None,
        "status": "operational"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    logger.debug("Health check endpoint accessed")
    return {
        "status": "healthy",
        "service": "hrms-backend",
        "version": "1.0.0"
    }


@app.get("/api/sync-status")
async def sync_status():
    """Check permission sync status."""
    try:
        from app.core.permission_sync import get_permission_sync_status
        return get_permission_sync_status()
    except ImportError:
        return {"error": "Permission sync module not available"}


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting HRMS FastAPI application on http://0.0.0.0:8001")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )