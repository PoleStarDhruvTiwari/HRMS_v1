import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.events import lifespan
from app.core.config import settings
from app.shared.middleware import setup_middleware
from app.shared.exceptions import setup_exception_handlers
from app.apis.auth.routers import router as auth_router
from app.apis.employees_profile.routers import router as employees_router


# Initialize logger
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="HRMS FastAPI Backend",
    description="Human Resource Management System API",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
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
app.include_router(employees_router)


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