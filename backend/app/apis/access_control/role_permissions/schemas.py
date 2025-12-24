# app/apis/access_control/role_permissions/schemas.py
"""
Role Permission Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# Request schemas
class RolePermissionAssign(BaseModel):
    """Assign permission to role."""
    role_id: int = Field(..., gt=0)
    permission_id: int = Field(..., gt=0)


class RolePermissionBulkAssign(BaseModel):
    """Assign multiple permissions to multiple roles."""
    role_ids: List[int] = Field(..., min_items=1)
    permission_ids: List[int] = Field(..., min_items=1)


class RolePermissionRemove(BaseModel):
    """Remove permission from role."""
    role_permission_id: Optional[int] = Field(None, gt=0)
    role_id: Optional[int] = Field(None, gt=0)
    permission_id: Optional[int] = Field(None, gt=0)


# Response schemas
class RolePermissionResponse(BaseModel):
    """Role permission response."""
    role_permission_id: int
    role_id: int
    role_name: Optional[str] = None
    role_code: Optional[str] = None
    permission_id: int
    permission_key: str
    permission_name: Optional[str] = None
    updated_by: int
    updated_by_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleWithPermissions(BaseModel):
    """Role with its permissions."""
    role_id: int
    role_code: str
    role_name: str
    permissions: List[RolePermissionResponse]
    total_permissions: int


class PermissionWithRoles(BaseModel):
    """Permission with roles that have it."""
    permission_id: int
    permission_key: str
    permission_name: Optional[str]
    roles: List[dict]
    total_roles: int