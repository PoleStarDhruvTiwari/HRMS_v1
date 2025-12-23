# app/apis/organization/teams/routes.py
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import TeamRepository
from .services import TeamService
from .schemas import TeamCreate, TeamUpdate, TeamResponse, TeamListResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/teams", tags=["Teams"])


def get_db() -> Session:
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_team_repository(db: Session = Depends(get_db)) -> TeamRepository:
    return TeamRepository(db)


def get_team_service(
    team_repo: TeamRepository = Depends(get_team_repository)
) -> TeamService:
    return TeamService(team_repo)


# **ESSENTIAL ENDPOINTS ONLY**

@router.get("/", response_model=TeamListResponse)
async def get_teams(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Get all teams with pagination.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Number of records to return (max 1000)
    - Returns: List of teams with member counts and pagination info
    """
    logger.info("Get all teams endpoint called")
    return team_service.get_teams(request, skip=skip, limit=limit)


@router.get("/search", response_model=TeamListResponse)
async def search_teams(
    request: Request,
    search: Optional[str] = Query(None, description="Search term for team name or description"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Search teams by name or description.
    
    - **search**: Search term for team name or description
    - Returns: Filtered teams with member counts and pagination info
    """
    logger.info("Search teams endpoint called")
    return team_service.search_teams(search or "", request, skip=skip, limit=limit)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    request: Request,
    team_service: TeamService = Depends(get_team_service)
):
    """
    Get team by ID.
    
    - **team_id**: Team ID
    - Returns: Team details with member count
    """
    logger.info(f"Get team endpoint called for ID: {team_id}")
    return team_service.get_team(team_id, request)


@router.post("/", response_model=TeamResponse, status_code=201)
async def create_team(
    request: Request,
    team_data: TeamCreate,
    team_service: TeamService = Depends(get_team_service)
):
    """
    Create a new team.
    
    - **Requires**: Admin privileges
    - **Request Body**: Team data
    - Returns: Created team
    """
    logger.info("Create team endpoint called")
    return team_service.create_team(team_data, request)


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    request: Request,
    team_data: TeamUpdate,
    team_service: TeamService = Depends(get_team_service)
):
    """
    Update team by ID.
    
    - **team_id**: Team ID
    - **Requires**: Admin privileges
    - **Request Body**: Team data to update
    - Returns: Updated team
    """
    logger.info(f"Update team endpoint called for ID: {team_id}")
    return team_service.update_team(team_id, team_data, request)


@router.delete("/{team_id}")
async def delete_team(
    team_id: int,
    request: Request,
    team_service: TeamService = Depends(get_team_service)
):
    """
    Delete team by ID.
    
    - **team_id**: Team ID
    - **Requires**: Admin privileges
    - Returns: Success message
    """
    logger.info(f"Delete team endpoint called for ID: {team_id}")
    return team_service.delete_team(team_id, request)