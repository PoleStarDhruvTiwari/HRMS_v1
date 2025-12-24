# app/apis/access_control/permissions/schemas.py
"""
Permission Schemas for API requests/responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PermissionStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"


# Base schema
class PermissionBase(BaseModel):
    permission_key: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None


# Response schemas
class PermissionResponse(PermissionBase):
    permission_id: int
    status: PermissionStatus
    updated_by: int
    updated_at: Optional[datetime] = None
    updated_by_name: Optional[str] = None
    role_count: Optional[int] = 0  # Number of roles with this permission
    
    model_config = ConfigDict(from_attributes=True)


class PermissionListResponse(BaseModel):
    permissions: List[PermissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PermissionGroupResponse(BaseModel):
    """Permissions grouped by module/category."""
    module: str
    permissions: List[PermissionResponse]


class PermissionSyncStatus(BaseModel):
    """Sync status between code and database."""
    code_total: int
    db_active: int
    db_deleted: int
    missing_in_db: List[str]
    extra_in_db: List[str]
    in_sync: bool