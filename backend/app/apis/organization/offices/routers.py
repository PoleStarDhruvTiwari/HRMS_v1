# app/apis/organization/offices/routes.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import OfficeRepository
from .services import OfficeService
from .schemas import OfficeCreate, OfficeUpdate, OfficeResponse, OfficeListResponse, NearbyOfficeRequest, NearbyOfficeResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/offices", tags=["Offices"])


def get_db() -> Session:
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_office_repository(db: Session = Depends(get_db)) -> OfficeRepository:
    return OfficeRepository(db)


def get_office_service(
    office_repo: OfficeRepository = Depends(get_office_repository)
) -> OfficeService:
    return OfficeService(office_repo)


# **ESSENTIAL ENDPOINTS ONLY**

@router.get("/", response_model=OfficeListResponse)
async def get_offices(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    office_service: OfficeService = Depends(get_office_service)
):
    """
    Get all offices with pagination.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Number of records to return (max 1000)
    - Returns: List of offices with pagination info
    """
    logger.info("Get all offices endpoint called")
    return office_service.get_offices(request, skip=skip, limit=limit)


@router.get("/search", response_model=OfficeListResponse)
async def search_offices(
    request: Request,
    search: Optional[str] = Query(None, description="Search term for office name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    office_service: OfficeService = Depends(get_office_service)
):
    """
    Search offices by name.
    
    - **search**: Search term for office name
    - Returns: Filtered offices with pagination info
    """
    logger.info("Search offices endpoint called")
    return office_service.search_offices(search or "", request, skip=skip, limit=limit)


@router.get("/{office_id}", response_model=OfficeResponse)
async def get_office(
    office_id: int,
    request: Request,
    office_service: OfficeService = Depends(get_office_service)
):
    """
    Get office by ID.
    
    - **office_id**: Office ID
    - Returns: Office details
    """
    logger.info(f"Get office endpoint called for ID: {office_id}")
    return office_service.get_office(office_id, request)


@router.post("/", response_model=OfficeResponse, status_code=201)
async def create_office(
    request: Request,
    office_data: OfficeCreate,
    office_service: OfficeService = Depends(get_office_service)
):
    """
    Create a new office.
    
    - **Requires**: Admin privileges
    - **Request Body**: Office data
    - Returns: Created office
    """
    logger.info("Create office endpoint called")
    return office_service.create_office(office_data, request)


@router.put("/{office_id}", response_model=OfficeResponse)
async def update_office(
    office_id: int,
    request: Request,
    office_data: OfficeUpdate,
    office_service: OfficeService = Depends(get_office_service)
):
    """
    Update office by ID.
    
    - **office_id**: Office ID
    - **Requires**: Admin privileges
    - **Request Body**: Office data to update
    - Returns: Updated office
    """
    logger.info(f"Update office endpoint called for ID: {office_id}")
    return office_service.update_office(office_id, office_data, request)


@router.delete("/{office_id}")
async def delete_office(
    office_id: int,
    request: Request,
    office_service: OfficeService = Depends(get_office_service)
):
    """
    Delete office by ID.
    
    - **office_id**: Office ID
    - **Requires**: Admin privileges
    - Returns: Success message
    """
    logger.info(f"Delete office endpoint called for ID: {office_id}")
    return office_service.delete_office(office_id, request)


@router.post("/nearby", response_model=list[NearbyOfficeResponse])
async def get_nearby_offices(
    request: Request,
    nearby_data: NearbyOfficeRequest,
    office_service: OfficeService = Depends(get_office_service)
):
    """
    Find offices near a location.
    
    - **Request Body**: Location coordinates and search radius
    - Returns: Nearby offices with distances
    """
    logger.info("Get nearby offices endpoint called")
    return office_service.get_nearby_offices(nearby_data, request)