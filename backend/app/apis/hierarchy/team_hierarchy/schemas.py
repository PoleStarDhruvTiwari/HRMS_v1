from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# Base schemas
class TeamHierarchyBase(BaseModel):
    child_team_id: int = Field(..., description="Child team ID")
    parent_team_id: Optional[int] = Field(None, description="Parent team ID")
    
    @validator('parent_team_id')
    def validate_not_self(cls, v, values):
        if v is not None and 'child_team_id' in values and v == values['child_team_id']:
            raise ValueError("Team cannot be parent of itself")
        return v

# Schema of incoming request data  for creating hierarchy for new team.
class NewTeamHierarchyCreate(BaseModel):
    """Schema for creating hierarchy for new team."""
    child_team_id: int = Field(..., description="New child team ID")
    first_parent_team_id: Optional[int] = Field(
        None, 
        description="ID of first parent team"
    )
    
    @validator('first_parent_team_id')
    def validate_not_self(cls, v, values):
        if v is not None and 'child_team_id' in values and v == values['child_team_id']:
            raise ValueError("Team cannot have itself as first parent")
        return v


class TeamHierarchyUpdate(BaseModel):
    """Schema for updating parent relationship."""
    parent_team_id: Optional[int] = Field(None, description="New parent team ID")
    
    @validator('parent_team_id')
    def validate_not_self_with_child_id(cls, v, values):
        if v is not None and 'child_team_id' in values and v == values['child_team_id']:
            raise ValueError("Team cannot be parent of itself")
        return v


# Response schemas
class TeamHierarchyResponse(TeamHierarchyBase):
    id: int
    depth_level: int
    updated_by: int
    updated_at: Optional[datetime] = None
    child_team_name: Optional[str] = None
    parent_team_name: Optional[str] = None
    updated_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class TeamChainResponse(BaseModel):
    child_team_id: int
    chain: List[Dict[str, Any]]
    total_levels: int


class ChildTeamsResponse(BaseModel):
    parent_team_id: int
    child_teams: List[Dict[str, Any]]
    total_count: int
    include_indirect: bool = False


class TeamTreeResponse(BaseModel):
    team_id: int
    team_name: Optional[str] = None
    depth: int
    children: List[Dict[str, Any]]


class TeamHierarchyListResponse(BaseModel):
    entries: List[TeamHierarchyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TeamHierarchyCreationResponse(BaseModel):
    message: str
    new_hierarchy_entries: List[TeamHierarchyResponse]