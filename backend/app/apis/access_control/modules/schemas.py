# app/apis/modules/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# Base schemas
class ModuleBase(BaseModel):
    module_name: str = Field(..., min_length=2, max_length=100)
    
    @validator('module_name')
    def module_name_title_case(cls, v):
        return v.strip().title()


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseModel):
    module_name: Optional[str] = Field(None, min_length=2, max_length=100)
    
    @validator('module_name')
    def module_name_title_case(cls, v):
        if v:
            return v.strip().title()
        return v


# Response schemas
class ModuleResponse(ModuleBase):
    module_id: int
    updated_by: int
    updated_at: Optional[datetime] = None
    updated_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ModuleListResponse(BaseModel):
    modules: List[ModuleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int