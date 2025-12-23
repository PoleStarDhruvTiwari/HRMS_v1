# app/apis/organization/shifts/schemas.py
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime, time


# Base schemas
class ShiftBase(BaseModel):
    shift_name: str = Field(..., min_length=2, max_length=10, pattern="^[A-Z0-9_]+$")
    start_time: time
    end_time: time
    
    @validator('shift_name')
    def shift_name_uppercase(cls, v):
        return v.upper()
    
    @validator('end_time')
    def validate_times(cls, v, values):
        if 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError('End time must be after start time')
        return v


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    shift_name: Optional[str] = Field(None, min_length=2, max_length=10, pattern="^[A-Z0-9_]+$")
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    
    @validator('shift_name')
    def shift_name_uppercase(cls, v):
        if v:
            return v.upper()
        return v
    
    @validator('end_time')
    def validate_times(cls, v, values):
        if 'start_time' in values and values['start_time'] and v:
            if v <= values['start_time']:
                raise ValueError('End time must be after start time')
        return v
    
    class Config:
        extra = "forbid"


# Response schemas
class ShiftResponse(ShiftBase):
    shift_id: int
    updated_by: int
    updated_at: Optional[datetime] = None
    updated_by_name: Optional[str] = None
    duration_hours: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class ShiftListResponse(BaseModel):
    shifts: List[ShiftResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Filter schemas
class ShiftFilter(BaseModel):
    search: Optional[str] = None
    shift_name: Optional[str] = None