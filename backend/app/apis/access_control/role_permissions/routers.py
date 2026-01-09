# app/apis/access_control/role_permissions/routes.py
"""
Role Permission API Endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import RolePermissionRepository
from .services import RolePermissionService
from .schemas import RolePermissionAssign, RolePermissionBulkAssign, RolePermissionRemove

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/role-permissions", tags=["Role Permissions"])


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


def get_role_permission_repository(db: Session = Depends(get_db)) -> RolePermissionRepository:
    return RolePermissionRepository(db)


def get_role_permission_service(
    role_perm_repo: RolePermissionRepository = Depends(get_role_permission_repository),
    db: Session = Depends(get_db)
) -> RolePermissionService:
    return RolePermissionService(role_perm_repo, db)


# ============ ESSENTIAL APIs ============

@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(
    role_id: int,
    request: Request,
    role_permission_service: RolePermissionService = Depends(get_role_permission_service)
):
    """
    Get all permissions assigned to a specific role.
    
    - **role_id**: Role ID
    - **Requires**: Admin access
    - Returns: List of permissions for the role
    """
    logger.info(f"Get permissions for role {role_id}")
    return role_permission_service.get_role_permissions(role_id, request)


@router.get("/permissions/{permission_id}/roles")
async def get_roles_with_permission(
    permission_id: int,
    request: Request,
    role_permission_service: RolePermissionService = Depends(get_role_permission_service)
):
    """
    Get all roles that have a specific permission.
    
    - **permission_id**: Permission ID
    - **Requires**: Admin access
    - Returns: List of roles with the permission
    """
    logger.info(f"Get roles with permission {permission_id}")
    return role_permission_service.get_roles_with_permission(permission_id, request)


@router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    request: Request,
    assign_data: RolePermissionAssign,
    role_permission_service: RolePermissionService = Depends(get_role_permission_service)
):
    """
    Assign a permission to a role.
    
    - **Requires**: Admin access
    - **Request Body**: role_id and permission_id
    - Returns: Success message
    """
    logger.info(f"Assign permission {assign_data.permission_id} to role {assign_data.role_id}")
    return role_permission_service.assign_permission(assign_data, request)


@router.post("/remove")
async def remove_permission_from_role(
    request: Request,
    remove_data: RolePermissionRemove,
    role_permission_service: RolePermissionService = Depends(get_role_permission_service)
):
    """
    Remove a permission from a role.
    
    - **Requires**: Admin access
    - **Request Body**: Either role_permission_id OR (role_id + permission_id)
    - Returns: Success message
    """
    logger.info(f"Remove permission: {remove_data}")
    return role_permission_service.remove_permission(remove_data, request)


# ============ UTILITY APIs ============

@router.post("/bulk-assign")
async def bulk_assign_permissions(
    request: Request,
    bulk_data: RolePermissionBulkAssign,
    role_permission_service: RolePermissionService = Depends(get_role_permission_service)
):
    """
    Assign multiple permissions to multiple roles in bulk.
    
    - **Requires**: Admin access
    - **Request Body**: List of role_ids and permission_ids
    - Returns: Summary of operations
    """
    logger.info(f"Bulk assign: {len(bulk_data.role_ids)} roles, {len(bulk_data.permission_ids)} permissions")
    return role_permission_service.bulk_assign_permissions(bulk_data, request)


@router.get("/check/{role_id}/{permission_key}")
async def check_role_has_permission(
    role_id: int,
    permission_key: str,
    request: Request,
    role_permission_service: RolePermissionService = Depends(get_role_permission_service)
):
    """
    Check if a role has a specific permission.
    
    - **role_id**: Role ID
    - **permission_key**: Permission key string
    - **Requires**: Admin access
    - Returns: Boolean indicating if role has the permission
    """
    logger.info(f"Check permission {permission_key} for role {role_id}")
    
    current_user_id = role_permission_service.get_current_user_id(request)
    role_permission_service.verify_admin_access(current_user_id)
    
    db = SessionLocal()
    try:
        repo = RolePermissionRepository(db)
        has_permission = repo.check_role_has_permission(role_id, permission_key)
        
        return {
            "role_id": role_id,
            "permission_key": permission_key,
            "has_permission": has_permission,
            "checked_by": current_user_id
        }
    finally:
        db.close()


@router.get("/search")
async def search_role_permissions(
    request: Request,
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    permission_key: Optional[str] = Query(None, description="Filter by permission key"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Page size"),
    role_permission_service: RolePermissionService = Depends(get_role_permission_service)
):
    """
    Search role permissions with filters.
    
    - **role_id**: Filter by specific role
    - **permission_key**: Filter by permission key
    - **skip**: Pagination offset
    - **limit**: Page size
    - **Requires**: Admin access
    - Returns: Filtered and paginated role permissions
    """
    logger.info(f"Search role permissions: role_id={role_id}, permission_key={permission_key}")
    
    current_user_id = role_permission_service.get_current_user_id(request)
    role_permission_service.verify_admin_access(current_user_id)
    
    db = SessionLocal()
    try:
        repo = RolePermissionRepository(db)
        results, total = repo.search_role_permissions(
            role_id=role_id,
            permission_key=permission_key,
            skip=skip,
            limit=limit
        )
        
        # Convert to response
        role_perms = []
        for rp in results:
            role_perms.append({
                "role_permission_id": rp.role_permission_id,
                "role_id": rp.role_id,
                "role_name": rp.role.role_name if rp.role else None,
                "role_code": rp.role.role_code if rp.role else None,
                "permission_id": rp.permission_id,
                "permission_key": rp.permission.permission_key if rp.permission else None,
                "permission_name": rp.permission.description if rp.permission else None,
                "updated_by": rp.updated_by,
                "updated_by_name": rp.updater.full_name if rp.updater else None,
                "updated_at": rp.updated_at
            })
        
        # Calculate pagination
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        return {
            "role_permissions": role_perms,
            "total": total,
            "page": current_page,
            "page_size": limit,
            "total_pages": total_pages,
            "filters": {
                "role_id": role_id,
                "permission_key": permission_key
            }
        }
        
    finally:
        db.close()