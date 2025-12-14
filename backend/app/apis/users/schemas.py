# app/apis/users/schemas.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# Enums for validation
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


# Base schema
class UserBase(BaseModel):
    global_employee_id: Optional[str] = Field(None, max_length=20)
    location_id: Optional[int] = None
    full_name: str = Field(..., max_length=150)
    email: EmailStr = Field(..., max_length=150)
    phone_number: Optional[str] = Field(None, max_length=20)
    team_id: Optional[int] = None
    vertical_id: Optional[int] = None
    designation_id: Optional[int] = None
    date_of_joining: date
    date_of_leaving: Optional[date] = None
    status: UserStatus = UserStatus.ACTIVE
    reporting_level1_id: Optional[int] = None
    reporting_level2_id: Optional[int] = None
    skills: Optional[Dict[str, Any]] = None
    certifications: Optional[Dict[str, Any]] = None
    experience_months: Optional[int] = Field(0, ge=0)
    role_id: Optional[int] = None
    is_active: bool = True
    is_admin: bool = False
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v and not v.replace('+', '').replace(' ', '').replace('-', '').isdigit():
            raise ValueError('Phone number must contain only digits and valid characters')
        return v


# Create schema
class UserCreate(UserBase):
    pass


# Update schema
class UserUpdate(BaseModel):
    global_employee_id: Optional[str] = Field(None, max_length=20)
    location_id: Optional[int] = None
    full_name: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = Field(None, max_length=150)
    phone_number: Optional[str] = Field(None, max_length=20)
    team_id: Optional[int] = None
    vertical_id: Optional[int] = None
    designation_id: Optional[int] = None
    date_of_joining: Optional[date] = None
    date_of_leaving: Optional[date] = None
    status: Optional[UserStatus] = None
    reporting_level1_id: Optional[int] = None
    reporting_level2_id: Optional[int] = None
    skills: Optional[Dict[str, Any]] = None
    certifications: Optional[Dict[str, Any]] = None
    experience_months: Optional[int] = Field(None, ge=0)
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    
    @validator('email')
    def email_lowercase(cls, v):
        if v:
            return v.lower()
        return v
    
    class Config:
        extra = "forbid"  # Don't allow extra fields


# Response schemas
class UserResponse(UserBase):
    user_id: int
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserProfileResponse(UserResponse):
    reporting_level1_name: Optional[str] = None
    reporting_level2_name: Optional[str] = None
    updater_name: Optional[str] = None


class UserBulkUpdate(BaseModel):
    user_ids: List[int]
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    team_id: Optional[int] = None
    role_id: Optional[int] = None


# Search and filter schemas
class UserFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[UserStatus] = None
    team_id: Optional[int] = None
    vertical_id: Optional[int] = None
    designation_id: Optional[int] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    date_of_joining_from: Optional[date] = None
    date_of_joining_to: Optional[date] = None


# Resume related schemas
class ResumeUpload(BaseModel):
    file_name: str
    file_type: str


class ResumeResponse(ResumeUpload):
    user_id: int
    uploaded_at: datetime
    file_size: Optional[int] = None