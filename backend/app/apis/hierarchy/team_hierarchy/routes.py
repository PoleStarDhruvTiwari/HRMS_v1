import logging
from typing import List, Optional,Dict, Any
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import TeamHierarchyRepository
from .services import TeamHierarchyService
from .schemas import (
    NewTeamHierarchyCreate,
    TeamHierarchyUpdate,
    TeamHierarchyResponse,
    TeamHierarchyListResponse,
    TeamChainResponse,
    ChildTeamsResponse,
    TeamHierarchyCreationResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/team-hierarchy", tags=["Team Hierarchy"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_hierarchy_repository(db: Session = Depends(get_db)) -> TeamHierarchyRepository:
    return TeamHierarchyRepository(db)


def get_hierarchy_service(
    hierarchy_repo: TeamHierarchyRepository = Depends(get_hierarchy_repository),
    db: Session = Depends(get_db)
) -> TeamHierarchyService:
    return TeamHierarchyService(hierarchy_repo, db)


@router.get("/", response_model=TeamHierarchyListResponse)
async def get_all_team_hierarchies(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    hierarchy_service: TeamHierarchyService = Depends(get_hierarchy_service)
):
    """
    Get all team hierarchy entries with pagination.
    
    Requires: team_hierarchy.view permission
    """
    logger.info("Get all team hierarchies endpoint called")
    return hierarchy_service.get_all_hierarchies(request, skip=skip, limit=limit)


@router.get("/team/{child_team_id}", response_model=List[TeamHierarchyResponse])
async def get_hierarchy_entries_for_team(
    request: Request,
    child_team_id: int,
    hierarchy_service: TeamHierarchyService = Depends(get_hierarchy_service)
):
    """
    Get ALL hierarchy entries for a specific team (multiple entries possible).
    
    Requires: team_hierarchy.view permission
    """
    logger.info(f"Get hierarchy entries for team endpoint called: {child_team_id}")
    return hierarchy_service.get_hierarchy_entries_for_team(child_team_id, request)


@router.post("/new-team", response_model=TeamHierarchyCreationResponse, status_code=201)
async def create_complete_hierarchy_for_team(
    request: Request,
    create_data: NewTeamHierarchyCreate,
    hierarchy_service: TeamHierarchyService = Depends(get_hierarchy_service)
):
    """
    Create COMPLETE hierarchy for a new team.
    
    Example: If new team (team3) has parent team2, and team2 has parent team1,
    this will create:
    - team3 under team2 (depth_level 1)
    - team3 under team1 (depth_level 2)
    
    Requires: team_hierarchy.create permission
    """
    logger.info("Create complete hierarchy for new team endpoint called")
    return hierarchy_service.create_complete_hierarchy_for_team(create_data, request)


@router.put("/team/{child_team_id}/parent", response_model=List[TeamHierarchyResponse])
async def update_parent_relationship(
    request: Request,
    child_team_id: int,
    update_data: TeamHierarchyUpdate,
    hierarchy_service: TeamHierarchyService = Depends(get_hierarchy_service)
):
    """
    Update parent relationship for a team.
    
    This will recreate the entire hierarchy chain for the team.
    
    Requires: team_hierarchy.update permission
    """
    logger.info(f"Update parent relationship endpoint called for team: {child_team_id}")
    return hierarchy_service.update_parent_relationship(child_team_id, update_data, request)


@router.get("/team/{child_team_id}/chain", response_model=TeamChainResponse)
async def get_team_chain(
    request: Request,
    child_team_id: int,
    hierarchy_service: TeamHierarchyService = Depends(get_hierarchy_service)
):
    """
    Get complete parent chain (all ancestors) for a team.
    
    Requires: team_hierarchy.view permission
    """
    logger.info(f"Get team chain endpoint called for team: {child_team_id}")
    return hierarchy_service.get_team_chain(child_team_id, request)


@router.get("/parent/{parent_team_id}/children", response_model=ChildTeamsResponse)
async def get_child_teams(
    request: Request,
    parent_team_id: int,
    include_indirect: bool = Query(False, description="Include indirect child teams"),
    hierarchy_service: TeamHierarchyService = Depends(get_hierarchy_service)
):
    """
    Get teams that report to a specific parent team.
    
    - Set include_indirect=true to get all child teams (direct and indirect)
    - Set include_indirect=false to get only direct child teams
    
    Requires: team_hierarchy.view permission
    """
    logger.info(f"Get child teams endpoint called for parent: {parent_team_id}")
    return hierarchy_service.get_child_teams(parent_team_id, include_indirect, request)


@router.get("/team-tree", response_model=Dict[str, Any])
async def get_team_tree(
    request: Request,
    top_team_id: Optional[int] = Query(None, description="Top team ID for tree"),
    hierarchy_service: TeamHierarchyService = Depends(get_hierarchy_service)
):
    """
    Get organizational tree of teams.
    
    - If top_team_id is provided: Get tree starting from that team
    - If top_team_id is not provided: Get complete team tree
    
    Requires: team_hierarchy.view permission
    """
    logger.info("Get team tree endpoint called")
    return hierarchy_service.get_team_tree(top_team_id, request)


@router.delete("/team/{child_team_id}", status_code=200)
async def delete_all_hierarchy_entries(
    request: Request,
    child_team_id: int,
    hierarchy_service: TeamHierarchyService = Depends(get_hierarchy_service)
):
    """
    Delete ALL hierarchy entries for a team.
    
    Requires: team_hierarchy.delete permission
    """
    logger.info(f"Delete all hierarchy entries endpoint called for team: {child_team_id}")
    return hierarchy_service.delete_hierarchy_entries(child_team_id, request)