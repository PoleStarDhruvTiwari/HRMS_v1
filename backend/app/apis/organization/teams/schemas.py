# app/apis/organization/teams/schemas.py
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime


# Base schemas
class TeamBase(BaseModel):
    team_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    
    @validator('team_name')
    def team_name_title_case(cls, v):
        return v.strip().title()


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    team_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    
    @validator('team_name')
    def team_name_title_case(cls, v):
        if v:
            return v.strip().title()
        return v
    
    class Config:
        extra = "forbid"


# Response schemas
class TeamResponse(TeamBase):
    team_id: int
    updated_by: int
    updated_at: Optional[datetime] = None
    updated_by_name: Optional[str] = None
    member_count: Optional[int] = 0  # Number of users in team
    
    model_config = ConfigDict(from_attributes=True)


class TeamListResponse(BaseModel):
    teams: List[TeamResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Filter schemas
class TeamFilter(BaseModel):
    search: Optional[str] = None
    team_name: Optional[str] = None