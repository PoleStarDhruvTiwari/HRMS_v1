# app/apis/organization/shifts/routes.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import ShiftRepository
from .services import ShiftService
from .schemas import ShiftCreate, ShiftUpdate, ShiftResponse, ShiftListResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/shifts", tags=["Shifts"])


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


def get_shift_repository(db: Session = Depends(get_db)) -> ShiftRepository:
    return ShiftRepository(db)


def get_shift_service(
    shift_repo: ShiftRepository = Depends(get_shift_repository)
) -> ShiftService:
    return ShiftService(shift_repo)


# **ESSENTIAL ENDPOINTS ONLY**

@router.get("/", response_model=ShiftListResponse)
async def get_shifts(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    shift_service: ShiftService = Depends(get_shift_service)
):
    """
    Get all shifts with pagination.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Number of records to return (max 1000)
    - Returns: List of shifts with pagination info
    """
    logger.info("Get all shifts endpoint called")
    return shift_service.get_shifts(request, skip=skip, limit=limit)


@router.get("/search", response_model=ShiftListResponse)
async def search_shifts(
    request: Request,
    search: Optional[str] = Query(None, description="Search term for shift name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    shift_service: ShiftService = Depends(get_shift_service)
):
    """
    Search shifts by name.
    
    - **search**: Search term for shift name
    - Returns: Filtered shifts with pagination info
    """
    logger.info("Search shifts endpoint called")
    return shift_service.search_shifts(search or "", request, skip=skip, limit=limit)


@router.get("/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: int,
    request: Request,
    shift_service: ShiftService = Depends(get_shift_service)
):
    """
    Get shift by ID.
    
    - **shift_id**: Shift ID
    - Returns: Shift details with duration
    """
    logger.info(f"Get shift endpoint called for ID: {shift_id}")
    return shift_service.get_shift(shift_id, request)


@router.post("/", response_model=ShiftResponse, status_code=201)
async def create_shift(
    request: Request,
    shift_data: ShiftCreate,
    shift_service: ShiftService = Depends(get_shift_service)
):
    """
    Create a new shift.
    
    - **Requires**: Admin privileges
    - **Request Body**: Shift data (name, start_time, end_time)
    - Returns: Created shift
    """
    logger.info("Create shift endpoint called")
    return shift_service.create_shift(shift_data, request)


@router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: int,
    request: Request,
    shift_data: ShiftUpdate,
    shift_service: ShiftService = Depends(get_shift_service)
):
    """
    Update shift by ID.
    
    - **shift_id**: Shift ID
    - **Requires**: Admin privileges
    - **Request Body**: Shift data to update
    - Returns: Updated shift
    """
    logger.info(f"Update shift endpoint called for ID: {shift_id}")
    return shift_service.update_shift(shift_id, shift_data, request)


@router.delete("/{shift_id}")
async def delete_shift(
    shift_id: int,
    request: Request,
    shift_service: ShiftService = Depends(get_shift_service)
):
    """
    Delete shift by ID.
    
    - **shift_id**: Shift ID
    - **Requires**: Admin privileges
    - Returns: Success message
    """
    logger.info(f"Delete shift endpoint called for ID: {shift_id}")
    return shift_service.delete_shift(shift_id, request)