from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime


# Base schemas
class EmployeeProfileBase(BaseModel):
    """Base schema for employee profile."""
    employee_id: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    nationality: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    personal_email: Optional[EmailStr] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_number: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[str] = Field(None, max_length=50)
    date_of_joining: Optional[date] = None
    employee_status: Optional[str] = Field("Active", max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    skills: Optional[str] = None


# Request schemas
class EmployeeProfileCreate(EmployeeProfileBase):
    """Schema for creating employee profile."""
    user_id: int


class EmployeeProfileUpdate(BaseModel):
    """Schema for updating employee profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    employee_status: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    skills: Optional[str] = None


# Response schemas
class EmployeeProfileResponse(EmployeeProfileBase):
    """Schema for employee profile response."""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeProfileDetailResponse(EmployeeProfileResponse):
    """Extended response with user information."""
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_picture: Optional[str] = None


class EmployeeDocumentBase(BaseModel):
    """Base schema for employee document."""
    document_type: str = Field(..., min_length=1, max_length=100)
    document_name: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=500)


class EmployeeDocumentResponse(EmployeeDocumentBase):
    """Schema for employee document response."""
    id: int
    employee_id: int
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime
    is_verified: bool
    verified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# List responses
class EmployeeListResponse(BaseModel):
    """Schema for paginated employee list."""
    items: List[EmployeeProfileResponse]
    total: int
    page: int
    size: int
    pages: int