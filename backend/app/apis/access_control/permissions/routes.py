# app/apis/access_control/permissions/routes.py
"""
READ-ONLY PERMISSION API ENDPOINTS

⚠️ SECURITY: These endpoints are READ-ONLY.
Permissions can only be modified via the automatic sync system.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.core.permissions import PermissionKey
from .repositories import PermissionRepository
from .services import PermissionService
from .schemas import PermissionResponse, PermissionListResponse, PermissionGroupResponse

logger = logging.getLogger(__name__)


# app/apis/access_control/permissions/routes.py
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.core.permissions import PermissionKey


# Create router
router = APIRouter(prefix="/api/permissions", tags=["Permissions"])


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


def get_permission_repository(db: Session = Depends(get_db)) -> PermissionRepository:
    return PermissionRepository(db)


def get_permission_service(
    permission_repo: PermissionRepository = Depends(get_permission_repository)
) -> PermissionService:
    return PermissionService(permission_repo)


@router.get("/system-defined")
async def get_system_permissions():
    """Get all permissions defined in the system (from code)."""
    return {
        "permissions": sorted(PermissionKey.values()),
        "total": len(PermissionKey.values())
    }

@router.get("/sync-status")
async def get_sync_status():
    """Check permission sync status between code and database."""
    from app.core.permission_sync import get_permission_sync_status
    return get_permission_sync_status()
    

@router.get("/", response_model=PermissionListResponse)
async def get_permissions(
    request: Request,
    active_only: bool = Query(True, description="Return only active permissions"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    Get all permissions (READ-ONLY).
    
    - **active_only**: Return only active permissions (default: True)
    - **skip**: Pagination offset
    - **limit**: Maximum records to return
    """
    logger.info("Get permissions endpoint called")
    return permission_service.get_permissions(
        request, 
        active_only=active_only,
        skip=skip, 
        limit=limit
    )


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    request: Request,
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    Get permission by ID (READ-ONLY).
    
    - **permission_id**: Permission ID
    """
    logger.info(f"Get permission endpoint called for ID: {permission_id}")
    return permission_service.get_permission(permission_id, request)


@router.get("/key/{permission_key}", response_model=PermissionResponse)
async def get_permission_by_key(
    permission_key: str,
    request: Request,
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    Get permission by key (READ-ONLY).
    
    - **permission_key**: Permission key (e.g., "attendance.mark")
    """
    logger.info(f"Get permission by key endpoint called: {permission_key}")
    return permission_service.get_permission_by_key(permission_key, request)


@router.get("/grouped/by-module", response_model=list[PermissionGroupResponse])
async def get_permissions_grouped_by_module(
    request: Request,
    active_only: bool = Query(True, description="Return only active permissions"),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """
    Get permissions grouped by module (READ-ONLY).
    
    - **active_only**: Return only active permissions
    """
    logger.info("Get permissions grouped by module endpoint called")
    return permission_service.get_permissions_grouped_by_module(request, active_only)


@router.get("/system/defined")
async def get_system_defined_permissions():
    """
    Get all permissions defined in the system (from code).
    
    This shows what permissions SHOULD exist according to code.
    Compare with /api/permissions/ to see database state.
    """
    logger.info("Get system defined permissions endpoint called")
    return {
        "permissions": sorted(PermissionKey.values()),
        "total": len(PermissionKey.values())
    }