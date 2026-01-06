from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# Base schemas
class EmployeeHierarchyBase(BaseModel):
    user_id: int = Field(..., description="Employee user ID")
    reporting_to_id: Optional[int] = Field(None, description="Manager's user ID")
    
    @validator('reporting_to_id')
    def validate_not_self(cls, v, values):
        if v is not None and 'user_id' in values and v == values['user_id']:
            raise ValueError("User cannot report to themselves")
        return v


class NewEmployeeHierarchyCreate(BaseModel):
    """Schema for creating hierarchy for new employee."""
    user_id: int = Field(..., description="New employee user ID")
    first_reportee_id: Optional[int] = Field(
        None, 
        description="ID of first employee who will report to the new employee"
    )
    
    @validator('first_reportee_id')
    def validate_not_self(cls, v, values):
        if v is not None and 'user_id' in values and v == values['user_id']:
            raise ValueError("New employee cannot have themselves as first reportee")
        return v


class EmployeeHierarchyUpdate(BaseModel):
    """Schema for updating reporting relationship."""
    reporting_to_id: Optional[int] = Field(None, description="New manager's user ID")
    
    @validator('reporting_to_id')
    def validate_not_self_with_user_id(cls, v, values):
        # Note: This validator works when user_id is passed in context
        if v is not None and 'user_id' in values and v == values['user_id']:
            raise ValueError("User cannot report to themselves")
        return v


# Response schemas
class EmployeeHierarchyResponse(EmployeeHierarchyBase):
    id: int
    depth: int
    updated_by: int
    updated_at: Optional[datetime] = None
    employee_name: Optional[str] = None
    reporting_to_name: Optional[str] = None
    updated_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReportingChainResponse(BaseModel):
    user_id: int
    chain: List[Dict[str, Any]]
    total_levels: int


class SubordinatesResponse(BaseModel):
    manager_id: int
    subordinates: List[Dict[str, Any]]
    total_count: int
    include_indirect: bool = False


class OrganizationalChartResponse(BaseModel):
    chart: List[Dict[str, Any]]
    total_employees: int
    max_depth: int


class EmployeeHierarchyListResponse(BaseModel):
    entries: List[EmployeeHierarchyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HierarchyCreationResponse(BaseModel):
    message: str
    new_employee_entry: EmployeeHierarchyResponse
    updated_reportee_entry: Optional[EmployeeHierarchyResponse] = None