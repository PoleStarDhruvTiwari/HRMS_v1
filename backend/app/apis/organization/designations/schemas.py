# app/apis/organization/designations/schemas.py
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime


# Base schemas
class DesignationBase(BaseModel):
    designation_code: str = Field(..., min_length=2, max_length=20)
    designation_name: str = Field(..., min_length=2, max_length=100)
    
    @validator('designation_code')
    def designation_code_uppercase(cls, v):
        return v.strip().upper()
    
    @validator('designation_name')
    def designation_name_title_case(cls, v):
        return v.strip().title()


class DesignationCreate(DesignationBase):
    pass


class DesignationUpdate(BaseModel):
    designation_code: Optional[str] = Field(None, min_length=2, max_length=20)
    designation_name: Optional[str] = Field(None, min_length=2, max_length=100)
    
    @validator('designation_code')
    def designation_code_uppercase(cls, v):
        if v:
            return v.strip().upper()
        return v
    
    @validator('designation_name')
    def designation_name_title_case(cls, v):
        if v:
            return v.strip().title()
        return v
    
    class Config:
        extra = "forbid"


# Response schemas
class DesignationResponse(DesignationBase):
    designation_id: int
    updated_by: int
    updated_at: Optional[datetime] = None
    updated_by_name: Optional[str] = None
    user_count: Optional[int] = 0  # Number of users with this designation
    
    model_config = ConfigDict(from_attributes=True)


class DesignationListResponse(BaseModel):
    designations: List[DesignationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Filter schemas
class DesignationFilter(BaseModel):
    search: Optional[str] = None
    designation_code: Optional[str] = None
    designation_name: Optional[str] = None