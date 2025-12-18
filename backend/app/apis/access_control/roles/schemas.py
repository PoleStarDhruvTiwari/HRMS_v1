# app/apis/roles/schemas.py
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime


# Base schemas
class RoleBase(BaseModel):
    role_code: str = Field(..., min_length=2, max_length=10, pattern="^[A-Z0-9_]+$")
    role_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    
    @validator('role_code')
    def role_code_uppercase(cls, v):
        return v.upper()
    
    @validator('role_name')
    def role_name_title_case(cls, v):
        return v.title()


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    role_code: Optional[str] = Field(None, min_length=2, max_length=10, pattern="^[A-Z0-9_]+$")
    role_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    
    @validator('role_code')
    def role_code_uppercase(cls, v):
        if v:
            return v.upper()
        return v
    
    @validator('role_name')
    def role_name_title_case(cls, v):
        if v:
            return v.title()
        return v
    
    class Config:
        extra = "forbid"  # Don't allow extra fields


# Response schemas
class RoleResponse(RoleBase):
    role_id: int
    updated_by_id: int
    updated_at: Optional[datetime] = None
    
    # Related data
    updated_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Filter schemas
class RoleFilter(BaseModel):
    search: Optional[str] = None
    role_code: Optional[str] = None
    role_name: Optional[str] = None


# Bulk operations
class RoleBulkUpdate(BaseModel):
    role_ids: List[int]
    description: Optional[str] = None


# Permission related (if you have permissions table)
class RolePermission(BaseModel):
    permission_id: int
    permission_name: str
    allowed: bool = True


class RoleWithPermissions(RoleResponse):
    permissions: Optional[List[RolePermission]] = None