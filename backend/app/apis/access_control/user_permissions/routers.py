# app/apis/access_control/user_permissions/routes.py
"""
User Permission API Endpoints with Token Verification
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import UserPermissionRepository
from .services import UserPermissionService
from .schemas import (
    UserPermissionGrant, UserPermissionRevoke, UserPermissionBulkGrant,
    UserPermissionResponse, EffectivePermissionsResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/user-permissions", tags=["User Permissions"])


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


def get_user_permission_repository(db: Session = Depends(get_db)) -> UserPermissionRepository:
    return UserPermissionRepository(db)


def get_user_permission_service(
    user_perm_repo: UserPermissionRepository = Depends(get_user_permission_repository),
    db: Session = Depends(get_db)
) -> UserPermissionService:
    return UserPermissionService(user_perm_repo, db)


# ============ ESSENTIAL APIs ============

@router.get("/users/{user_id}/permissions", response_model=list[UserPermissionResponse])
async def get_user_permissions(
    user_id: int,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Get all permissions directly assigned to a specific user.
    
    - **user_id**: User ID
    - **Requires**: Valid JWT token (admin for other users, anyone for themselves)
    - Returns: List of direct permissions for the user
    """
    logger.info(f"Get permissions for user {user_id}")
    return user_permission_service.get_user_permissions(user_id, request)


@router.get("/permissions/{permission_id}/users")
async def get_users_with_permission(
    permission_id: int,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Get all users who have a specific permission directly assigned.
    
    - **permission_id**: Permission ID
    - **Requires**: Valid JWT token with admin access
    - Returns: List of users with the permission
    """
    logger.info(f"Get users with permission {permission_id}")
    return user_permission_service.get_users_with_permission(permission_id, request)


@router.post("/grant", response_model=UserPermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_permission_to_user(
    request: Request,
    grant_data: UserPermissionGrant,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Grant a permission directly to a user (bypassing roles).
    
    - **Requires**: Valid JWT token with admin access
    - **Request Body**: user_id and permission_id
    - Returns: Created user permission record
    """
    logger.info(f"Grant permission {grant_data.permission_id} to user {grant_data.user_id}")
    return user_permission_service.grant_permission(grant_data, request)


@router.post("/revoke")
async def revoke_permission_from_user(
    request: Request,
    revoke_data: UserPermissionRevoke,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Revoke a directly granted permission from a user.
    
    - **Requires**: Valid JWT token with admin access
    - **Request Body**: Either user_permission_id OR (user_id + permission_id)
    - Returns: Success message
    """
    logger.info(f"Revoke permission: {revoke_data}")
    return user_permission_service.revoke_permission(revoke_data, request)


@router.delete("/{user_permission_id}")
async def delete_user_permission_record(
    user_permission_id: int,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Hard delete a user permission record (for cleanup).
    
    - **user_permission_id**: User Permission ID
    - **Requires**: Valid JWT token with admin access
    - Returns: Success message
    """
    logger.info(f"Delete user permission {user_permission_id}")
    return user_permission_service.delete_user_permission(user_permission_id, request)


@router.get("/users/{user_id}/effective", response_model=EffectivePermissionsResponse)
async def get_user_effective_permissions(
    user_id: int,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Get user's effective permissions (roles + direct permissions).
    
    - **user_id**: User ID
    - **Requires**: Valid JWT token (admin for other users, anyone for themselves)
    - Returns: Combined permissions from roles and direct assignments
    """
    logger.info(f"Get effective permissions for user {user_id}")
    return user_permission_service.get_user_effective_permissions(user_id, request)


# ============ UTILITY APIs ============

@router.post("/bulk-grant")
async def bulk_grant_permissions(
    request: Request,
    bulk_data: UserPermissionBulkGrant,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Grant multiple permissions to multiple users in bulk.
    
    - **Requires**: Valid JWT token with admin access
    - **Request Body**: List of user_ids and permission_ids
    - Returns: Summary of operations
    """
    logger.info(f"Bulk grant: {len(bulk_data.user_ids)} users, {len(bulk_data.permission_ids)} permissions")
    return user_permission_service.bulk_grant_permissions(bulk_data, request)


@router.get("/check/{user_id}/{permission_key}")
async def check_user_has_permission(
    user_id: int,
    permission_key: str,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Check if a user has a specific permission (directly or via roles).
    
    - **user_id**: User ID
    - **permission_key**: Permission key string (e.g., "user.create")
    - **Requires**: Valid JWT token (admin for other users, anyone for themselves)
    - Returns: Boolean indicating if user has the permission
    """
    logger.info(f"Check permission {permission_key} for user {user_id}")
    return user_permission_service.check_user_permission(user_id, permission_key, request)


@router.get("/search")
async def search_user_permissions(
    request: Request,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    permission_key: Optional[str] = Query(None, description="Filter by permission key"),
    status: Optional[str] = Query("active", description="Filter by status: active, revoked, all"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Page size"),
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Search user permissions with filters.
    
    - **user_id**: Filter by specific user
    - **permission_key**: Filter by permission key
    - **status**: active, revoked, or all
    - **skip**: Pagination offset
    - **limit**: Page size
    - **Requires**: Valid JWT token with admin access
    - Returns: Filtered and paginated user permissions
    """
    logger.info(f"Search user permissions: user_id={user_id}, permission_key={permission_key}")
    
    # This route needs admin access - service will verify
    current_user_id = user_permission_service.get_current_user_id(request)
    user_permission_service.verify_admin_access(current_user_id)
    
    db = SessionLocal()
    try:
        repo = UserPermissionRepository(db)
        active_only = status.lower() == "active" if status else True
        
        results, total = repo.search_user_permissions(
            user_id=user_id,
            permission_key=permission_key,
            active_only=active_only,
            skip=skip,
            limit=limit
        )
        
        # Convert to response
        user_perms = []
        for up in results:
            user_perms.append({
                "user_permission_id": up.user_permission_id,
                "user_id": up.user_id,
                "user_name": up.user.full_name if up.user else None,
                "user_email": up.user.email if up.user else None,
                "permission_id": up.permission_id,
                "permission_key": up.permission.permission_key if up.permission else None,
                "permission_name": up.permission.description if up.permission else None,
                "granted_by": up.granted_by,
                "granted_by_name": up.granter.full_name if up.granter else None,
                "granted_at": up.granted_at,
                "revoked_at": up.revoked_at,
                "status": "active" if not up.revoked_at else "revoked"
            })
        
        # Calculate pagination
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        return {
            "user_permissions": user_perms,
            "total": total,
            "page": current_page,
            "page_size": limit,
            "total_pages": total_pages,
            "filters": {
                "user_id": user_id,
                "permission_key": permission_key,
                "status": status
            }
        }
        
    finally:
        db.close()



# app/apis/access_control/user_permissions/routes.py
# Add these endpoints:

@router.post("/users/{user_id}/grant-extra/{permission_id}")
async def grant_extra_permission(
    user_id: int,
    permission_id: int,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Grant an extra permission to user (adds to role permissions).
    
    - **user_id**: User ID
    - **permission_id**: Permission ID to grant as extra
    - **Requires**: Admin access
    - Returns: Success message
    """
    logger.info(f"Grant extra permission {permission_id} to user {user_id}")
    return user_permission_service.grant_extra_permission(user_id, permission_id, request)


@router.post("/users/{user_id}/revoke-role/{permission_id}")
async def revoke_role_permission(
    user_id: int,
    permission_id: int,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Revoke a permission from user's role permissions.
    
    - **user_id**: User ID
    - **permission_id**: Permission ID to revoke from role
    - **Requires**: Admin access
    - Returns: Success message
    """
    logger.info(f"Revoke role permission {permission_id} from user {user_id}")
    return user_permission_service.revoke_role_permission(user_id, permission_id, request)


@router.get("/users/{user_id}/summary")
async def get_user_permission_summary(
    user_id: int,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Get detailed summary of user's permissions with status.
    
    - **user_id**: User ID
    - **Requires**: User can view own, admin can view anyone
    - Returns: Detailed permission summary with role, granted, revoked permissions
    """
    logger.info(f"Get permission summary for user {user_id}")
    return user_permission_service.get_user_permission_summary(user_id, request)


@router.delete("/users/{user_id}/permissions/{permission_id}")
async def remove_user_permission(
    user_id: int,
    permission_id: int,
    request: Request,
    user_permission_service: UserPermissionService = Depends(get_user_permission_service)
):
    """
    Remove a user permission record (both granted and revoked).
    
    - **user_id**: User ID
    - **permission_id**: Permission ID to remove
    - **Requires**: Admin access
    - Returns: Success message
    """
    logger.info(f"Remove permission {permission_id} from user {user_id}")
    
    current_user_id = user_permission_service.get_current_user_id(request)
    user_permission_service.verify_admin_access(current_user_id)
    
    db = SessionLocal()
    try:
        repo = UserPermissionRepository(db)
        success = repo.remove_user_permission(user_id, permission_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User permission not found"
            )
        
        return {"message": "User permission removed successfully"}
    finally:
        db.close()