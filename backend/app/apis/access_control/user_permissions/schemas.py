# app/apis/access_control/user_permissions/schemas.py
"""
User Permission Schemas
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime


# Request schemas
class UserPermissionGrant(BaseModel):
    """Grant permission to user."""
    user_id: int = Field(..., gt=0)
    permission_id: int = Field(..., gt=0)


class UserPermissionRevoke(BaseModel):
    """Revoke permission from user."""
    user_permission_id: int = Field(..., gt=0)
    # Or alternative: user_id + permission_id
    user_id: Optional[int] = Field(None, gt=0)
    permission_id: Optional[int] = Field(None, gt=0)
    
    @validator('user_id')
    def validate_user_id(cls, v, values):
        if v is None and values.get('permission_id') is None:
            raise ValueError("Either user_permission_id OR (user_id + permission_id) must be provided")
        return v


class UserPermissionBulkGrant(BaseModel):
    """Grant multiple permissions to multiple users."""
    user_ids: List[int] = Field(..., min_items=1)
    permission_ids: List[int] = Field(..., min_items=1)


# Response schemas
class UserPermissionResponse(BaseModel):
    """User permission response."""
    user_permission_id: int
    user_id: int
    permission_id: int
    permission_key: str
    permission_name: Optional[str] = None
    granted_by: int
    granted_by_name: Optional[str] = None
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    status: str  # 'active' or 'revoked'
    
    model_config = ConfigDict(from_attributes=True)


class UserWithPermissions(BaseModel):
    """User with their direct permissions."""
    user_id: int
    full_name: str
    email: str
    permissions: List[UserPermissionResponse]


class PermissionWithUsers(BaseModel):
    """Permission with users who have it directly."""
    permission_id: int
    permission_key: str
    permission_name: Optional[str]
    users: List[dict]  # List of user info


class EffectivePermissionsResponse(BaseModel):
    """User's effective permissions (roles + direct)."""
    user_id: int
    full_name: str
    email: str
    direct_permissions: List[dict]
    role_permissions: List[dict]
    all_permissions: List[str]  # Combined unique permission keys
    total_permissions: int


# Filter schemas
class UserPermissionFilter(BaseModel):
    user_id: Optional[int] = None
    permission_id: Optional[int] = None
    status: Optional[str] = None  # 'active', 'revoked', 'all'
    search: Optional[str] = None