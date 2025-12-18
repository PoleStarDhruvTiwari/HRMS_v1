# app/apis/roles/routes.py
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import RoleRepository
from .services import RoleService
from .schemas import (
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
    RoleFilter, RoleBulkUpdate
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/roles", tags=["Roles"])


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


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    return RoleRepository(db)


def get_role_service(
    role_repo: RoleRepository = Depends(get_role_repository)
) -> RoleService:
    return RoleService(role_repo)


@router.get("/", response_model=List[RoleResponse])
async def get_roles(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    role_service: RoleService = Depends(get_role_service)
):
    """
    Get all roles with pagination.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Number of records to return (max 1000)
    - Returns: List of roles
    """
    logger.info("Get all roles endpoint called")
    return role_service.get_roles(request, skip=skip, limit=limit)


@router.get("/search", response_model=RoleListResponse)
async def search_roles(
    request: Request,
    search: Optional[str] = Query(None, description="Search term (code, name, description)"),
    role_code: Optional[str] = Query(None, description="Filter by role code"),
    role_name: Optional[str] = Query(None, description="Filter by role name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    sort_by: str = Query("role_code", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    role_service: RoleService = Depends(get_role_service)
):
    """
    Search roles with filters.
    
    - **search**: Search in code, name, description
    - **role_code**: Filter by role code
    - **role_name**: Filter by role name
    - **sort_by**: Field to sort by
    - **sort_order**: Sort order
    - Returns: Filtered and sorted roles with pagination
    """
    logger.info("Search roles endpoint called")
    
    # Create filter object
    filters = RoleFilter(
        search=search,
        role_code=role_code,
        role_name=role_name
    )
    
    return role_service.search_roles(
        filters=filters,
        request=request,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    request: Request,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Get role by ID.
    
    - **role_id**: Role ID
    - Returns: Role details
    """
    logger.info(f"Get role endpoint called for ID: {role_id}")
    return role_service.get_role(role_id, request)


@router.get("/code/{role_code}", response_model=RoleResponse)
async def get_role_by_code(
    role_code: str,
    request: Request,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Get role by code.
    
    - **role_code**: Role code (uppercase)
    - Returns: Role details
    """
    logger.info(f"Get role by code endpoint called: {role_code}")
    
    # Get role by code
    from app.database.session import SessionLocal
    from .repositories import RoleRepository
    
    db = SessionLocal()
    try:
        role_repo = RoleRepository(db)
        role = role_repo.get_by_code(role_code)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        return role_service.get_role(role.role_id, request)
    finally:
        db.close()


@router.post("/", response_model=RoleResponse, status_code=201)
async def create_role(
    request: Request,
    role_data: RoleCreate,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Create a new role.
    
    - **Requires**: Admin privileges
    - **Request Body**: Role data
    - Returns: Created role
    """
    logger.info("Create role endpoint called")
    return role_service.create_role(role_data, request)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    request: Request,
    role_data: RoleUpdate,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Update role by ID.
    
    - **role_id**: Role ID
    - **Requires**: Admin privileges
    - **Request Body**: Role data to update
    - Returns: Updated role
    """
    logger.info(f"Update role endpoint called for ID: {role_id}")
    return role_service.update_role(role_id, role_data, request)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    request: Request,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Delete role by ID.
    
    - **role_id**: Role ID
    - **Requires**: Admin privileges
    - Returns: Success message
    """
    logger.info(f"Delete role endpoint called for ID: {role_id}")
    return role_service.delete_role(role_id, request)


@router.post("/bulk-update")
async def bulk_update_roles(
    request: Request,
    bulk_data: RoleBulkUpdate,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Update multiple roles at once.
    
    - **Requires**: Admin privileges
    - **Request Body**: List of role IDs and fields to update
    - Returns: Update statistics
    """
    logger.info("Bulk update roles endpoint called")
    return role_service.bulk_update_roles(bulk_data, request)


@router.get("/stats/counts")
async def get_role_counts(
    request: Request,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Get role statistics.
    
    - **Requires**: Admin privileges
    - Returns: Role counts and statistics
    """
    logger.info("Get role counts endpoint called")
    return role_service.get_role_counts(request)


@router.get("/default-roles", response_model=List[RoleResponse])
async def get_default_roles(
    request: Request,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Get default system roles.
    
    - Returns: List of default roles (ADMIN, MANAGER, EMPLOYEE, VIEWER)
    """
    logger.info("Get default roles endpoint called")
    return role_service.get_default_roles()


@router.post("/initialize-defaults")
async def initialize_default_roles(
    request: Request,
    role_service: RoleService = Depends(get_role_service)
):
    """
    Initialize default system roles if they don't exist.
    
    - **Requires**: Admin privileges
    - Returns: Initialization status
    """
    logger.info("Initialize default roles endpoint called")
    
    try:
        # Get current user ID and verify admin
        current_user_id = role_service.get_current_user_id(request)
        role_service.verify_admin_access(current_user_id)
        
        # Default roles to create
        default_roles = [
            {
                "role_code": "ADMIN",
                "role_name": "Administrator",
                "description": "Full system access with administrative privileges"
            },
            {
                "role_code": "MANAGER",
                "role_name": "Manager",
                "description": "Team management with reporting and approval access"
            },
            {
                "role_code": "EMPLOYEE",
                "role_name": "Employee",
                "description": "Regular employee with standard access"
            },
            {
                "role_code": "VIEWER",
                "role_name": "Viewer",
                "description": "Read-only access for viewing reports"
            }
        ]
        
        created_count = 0
        from app.database.session import SessionLocal
        from .repositories import RoleRepository
        
        db = SessionLocal()
        try:
            role_repo = RoleRepository(db)
            
            for role_data in default_roles:
                # Check if role already exists
                existing_role = role_repo.get_by_code(role_data["role_code"])
                if not existing_role:
                    # Create the role
                    role_repo.create(role_data, updated_by_id=current_user_id)
                    created_count += 1
                    logger.info(f"Created default role: {role_data['role_code']}")
                else:
                    logger.info(f"Role already exists: {role_data['role_code']}")
            
            db.commit()
            
            return {
                "message": f"Default roles initialized. Created {created_count} new roles.",
                "created_count": created_count,
                "total_defaults": len(default_roles)
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error initializing default roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/check-available/{role_code}")
async def check_role_code_available(
    role_code: str,
    request: Request
):
    """
    Check if a role code is available.
    
    - **role_code**: Role code to check
    - Returns: Availability status
    """
    logger.info(f"Check role code available endpoint called: {role_code}")
    
    from app.database.session import SessionLocal
    from .repositories import RoleRepository
    
    db = SessionLocal()
    try:
        role_repo = RoleRepository(db)
        role = role_repo.get_by_code(role_code)
        
        return {
            "role_code": role_code,
            "available": role is None,
            "message": "Role code is available" if role is None else "Role code already exists"
        }
    finally:
        db.close()