# app/apis/organization/designations/routes.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import DesignationRepository
from .services import DesignationService
from .schemas import DesignationCreate, DesignationUpdate, DesignationResponse, DesignationListResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/designations", tags=["Designations"])


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


def get_designation_repository(db: Session = Depends(get_db)) -> DesignationRepository:
    return DesignationRepository(db)


def get_designation_service(
    designation_repo: DesignationRepository = Depends(get_designation_repository)
) -> DesignationService:
    return DesignationService(designation_repo)


# **ESSENTIAL ENDPOINTS**

@router.get("/", response_model=DesignationListResponse)
async def get_designations(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    designation_service: DesignationService = Depends(get_designation_service)
):
    """
    Get all designations with pagination.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Number of records to return (max 1000)
    - Returns: List of designations with user counts and pagination info
    """
    logger.info("Get all designations endpoint called")
    return designation_service.get_designations(request, skip=skip, limit=limit)


@router.get("/search", response_model=DesignationListResponse)
async def search_designations(
    request: Request,
    search: Optional[str] = Query(None, description="Search term for designation code or name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    designation_service: DesignationService = Depends(get_designation_service)
):
    """
    Search designations by code or name.
    
    - **search**: Search term for designation code or name
    - Returns: Filtered designations with user counts and pagination info
    """
    logger.info("Search designations endpoint called")
    return designation_service.search_designations(search or "", request, skip=skip, limit=limit)


@router.get("/{designation_id}", response_model=DesignationResponse)
async def get_designation(
    designation_id: int,
    request: Request,
    designation_service: DesignationService = Depends(get_designation_service)
):
    """
    Get designation by ID.
    
    - **designation_id**: Designation ID
    - Returns: Designation details with user count
    """
    logger.info(f"Get designation endpoint called for ID: {designation_id}")
    return designation_service.get_designation(designation_id, request)


@router.post("/", response_model=DesignationResponse, status_code=201)
async def create_designation(
    request: Request,
    designation_data: DesignationCreate,
    designation_service: DesignationService = Depends(get_designation_service)
):
    """
    Create a new designation.
    
    - **Requires**: Admin privileges
    - **Request Body**: Designation data
    - Returns: Created designation
    """
    logger.info("Create designation endpoint called")
    return designation_service.create_designation(designation_data, request)


@router.put("/{designation_id}", response_model=DesignationResponse)
async def update_designation(
    designation_id: int,
    request: Request,
    designation_data: DesignationUpdate,
    designation_service: DesignationService = Depends(get_designation_service)
):
    """
    Update designation by ID.
    
    - **designation_id**: Designation ID
    - **Requires**: Admin privileges
    - **Request Body**: Designation data to update
    - Returns: Updated designation
    """
    logger.info(f"Update designation endpoint called for ID: {designation_id}")
    return designation_service.update_designation(designation_id, designation_data, request)


@router.delete("/{designation_id}")
async def delete_designation(
    designation_id: int,
    request: Request,
    designation_service: DesignationService = Depends(get_designation_service)
):
    """
    Delete designation by ID.
    
    - **designation_id**: Designation ID
    - **Requires**: Admin privileges
    - Returns: Success message
    """
    logger.info(f"Delete designation endpoint called for ID: {designation_id}")
    return designation_service.delete_designation(designation_id, request)


# **SPECIAL ENDPOINTS**

@router.get("/code/{designation_code}", response_model=DesignationResponse)
async def get_designation_by_code(
    designation_code: str,
    request: Request,
    designation_service: DesignationService = Depends(get_designation_service)
):
    """
    Get designation by code.
    
    - **designation_code**: Designation code
    - Returns: Designation details with user count
    """
    logger.info(f"Get designation by code endpoint called: {designation_code}")
    
    # Get current user ID for auth check
    designation_service.get_current_user_id(request)
    
    db = SessionLocal()
    try:
        designation_repo = DesignationRepository(db)
        designation = designation_repo.get_by_code(designation_code)
        
        if not designation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Designation not found"
            )
        
        # Get user count
        user_count = designation_repo.get_user_count(designation.designation_id)
        
        # Convert to response
        response_data = {
            'designation_id': designation.designation_id,
            'designation_code': designation.designation_code,
            'designation_name': designation.designation_name,
            'updated_by': designation.updated_by,
            'updated_at': designation.updated_at,
            'user_count': user_count
        }
        
        # Add related data if available
        if hasattr(designation, 'updater') and designation.updater:
            response_data['updated_by_name'] = designation.updater.full_name
        
        return DesignationResponse(**response_data)
    finally:
        db.close()