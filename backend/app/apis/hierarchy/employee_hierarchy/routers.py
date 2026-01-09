import logging
from typing import List
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import EmployeeHierarchyRepository
from .services import EmployeeHierarchyService
from .schemas import (
    NewEmployeeHierarchyCreate,
    EmployeeHierarchyResponse,
    EmployeeHierarchyListResponse,
    HierarchyCreationResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hierarchy", tags=["Employee Hierarchy"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_hierarchy_repository(db: Session = Depends(get_db)) -> EmployeeHierarchyRepository:
    return EmployeeHierarchyRepository(db)


def get_hierarchy_service(
    hierarchy_repo: EmployeeHierarchyRepository = Depends(get_hierarchy_repository),
    db: Session = Depends(get_db)
) -> EmployeeHierarchyService:
    return EmployeeHierarchyService(hierarchy_repo, db)


@router.get("/", response_model=EmployeeHierarchyListResponse)
async def get_all_hierarchies(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    hierarchy_service: EmployeeHierarchyService = Depends(get_hierarchy_service)
):
    """
    Get all hierarchy entries with pagination.
    
    Requires: hierarchy.view permission
    """
    logger.info("Get all hierarchies endpoint called")
    return hierarchy_service.get_all_hierarchies(request, skip=skip, limit=limit)


@router.get("/user/{user_id}", response_model=List[EmployeeHierarchyResponse])
async def get_hierarchy_entries_for_user(
    request: Request,
    user_id: int,
    hierarchy_service: EmployeeHierarchyService = Depends(get_hierarchy_service)
):
    """
    Get ALL hierarchy entries for a specific user (multiple entries possible).
    
    Example: If user1 reports to user2 (depth 1), user3 (depth 2), user4 (depth 3),
    this endpoint returns all 3 entries.
    
    Requires: hierarchy.view permission
    """
    logger.info(f"Get hierarchy entries for user endpoint called: {user_id}")
    return hierarchy_service.get_hierarchy_entries_for_user(user_id, request)


@router.post("/new-employee", response_model=HierarchyCreationResponse, status_code=201)
async def create_complete_hierarchy_for_new_employee(
    request: Request,
    create_data: NewEmployeeHierarchyCreate,
    hierarchy_service: EmployeeHierarchyService = Depends(get_hierarchy_service)
):
    """
    Create COMPLETE reporting chain for a new employee.
    
    Example: If new employee (user1) reports to user2, and user2 reports to user3,
    this will create:
    - user1 reports to user2 (depth 1)
    - user1 reports to user3 (depth 2)
    - user1 reports to user4 (depth 3) ... and so on up the chain
    
    Requires: hierarchy.create permission
    """
    logger.info("Create complete hierarchy for new employee endpoint called")
    return hierarchy_service.create_complete_hierarchy_for_new_employee(create_data, request)


@router.delete("/user/{user_id}", status_code=200)
async def delete_all_hierarchy_entries(
    request: Request,
    user_id: int,
    hierarchy_service: EmployeeHierarchyService = Depends(get_hierarchy_service)
):
    """
    Delete ALL hierarchy entries for a user.
    
    Requires: hierarchy.delete permission
    """
    logger.info(f"Delete all hierarchy entries endpoint called for user: {user_id}")
    return hierarchy_service.delete_hierarchy_entries(user_id, request)


@router.get("/manager/{manager_id}/reportees", response_model=List[EmployeeHierarchyResponse])
async def get_reportees_by_manager(
    request: Request,
    manager_id: int,
    hierarchy_service: EmployeeHierarchyService = Depends(get_hierarchy_service)
):
    """
    Get all employees who directly report to a specific manager.
    
    Requires: hierarchy.view permission
    """
    logger.info(f"Get reportees by manager endpoint called for manager: {manager_id}")
    
    try:
        current_user_id = hierarchy_service.get_current_user_id(request)
        hierarchy_service.verify_permission(current_user_id, "hierarchy.view")
        
        # Get entries using repository
        entries = hierarchy_service.hierarchy_repo.get_users_by_manager(manager_id)
        
        if not entries:
            raise HTTPException(
                status_code=404,
                detail=f"No employees found reporting to manager: {manager_id}"
            )
        
        # Prepare responses
        responses = []
        for entry in entries:
            response_data = {
                "id": entry.id,
                "user_id": entry.user_id,
                "reporting_to_id": entry.reporting_to_id,
                "depth": entry.depth,
                "updated_by": entry.updated_by,
                "updated_at": entry.updated_at,
                "employee_name": hierarchy_service._get_user_name(entry.user_id),
                "reporting_to_name": hierarchy_service._get_user_name(entry.reporting_to_id) if entry.reporting_to_id else None,
                "updated_by_name": hierarchy_service._get_user_name(entry.updated_by) if entry.updated_by else None
            }
            responses.append(EmployeeHierarchyResponse(**response_data))
        
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting reportees by manager: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )