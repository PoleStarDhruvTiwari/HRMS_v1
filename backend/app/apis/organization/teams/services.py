# app/apis/organization/teams/services.py
import logging
from typing import List
from fastapi import HTTPException, status

from app.core.security import security_service
from .repositories import TeamRepository
from .schemas import TeamCreate, TeamUpdate, TeamResponse, TeamListResponse

logger = logging.getLogger(__name__)


class TeamService:
    """Service for team business logic."""
    
    def __init__(self, team_repo: TeamRepository):
        self.team_repo = team_repo
    
    def get_current_user_id(self, request) -> int:
        """Extract current user ID from request."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        access_token = security_service.extract_token_from_header(auth_header)
        payload = security_service.verify_local_token(access_token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return user_id
    
    def verify_admin_access(self, user_id: int):
        """Verify user has admin privileges."""
        from app.database.session import SessionLocal
        from app.apis.auth.models import ExistingUser
        
        db = SessionLocal()
        try:
            user = db.query(ExistingUser).filter(ExistingUser.user_id == user_id).first()
            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
        finally:
            db.close()
    
    def get_team(self, team_id: int, request) -> TeamResponse:
        """Get team by ID."""
        logger.debug(f"Getting team: {team_id}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            team = self.team_repo.get_by_id(team_id)
            if not team:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found"
                )
            
            # Get member count
            member_count = self.team_repo.get_member_count(team_id)
            
            # Convert to response
            response_data = {
                'team_id': team.team_id,
                'team_name': team.team_name,
                'description': team.description,
                'updated_by': team.updated_by,
                'updated_at': team.updated_at,
                'member_count': member_count
            }
            
            # Add related data if available
            if hasattr(team, 'updater') and team.updater:
                response_data['updated_by_name'] = team.updater.full_name
            
            return TeamResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting team {team_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_teams(self, request, skip: int = 0, limit: int = 100) -> TeamListResponse:
        """Get all teams with pagination."""
        logger.debug(f"Getting teams (skip: {skip}, limit: {limit})")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            teams_with_counts = self.team_repo.get_teams_with_member_counts(skip=skip, limit=limit)
            total = self.team_repo.get_count()
            
            # Convert to responses
            team_responses = []
            for team, member_count in teams_with_counts:
                response_data = {
                    'team_id': team.team_id,
                    'team_name': team.team_name,
                    'description': team.description,
                    'updated_by': team.updated_by,
                    'updated_at': team.updated_at,
                    'member_count': member_count
                }
                
                # Add related data if available
                if hasattr(team, 'updater') and team.updater:
                    response_data['updated_by_name'] = team.updater.full_name
                
                team_responses.append(TeamResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return TeamListResponse(
                teams=team_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting teams: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def search_teams(self, search_term: str, request, skip: int = 0, limit: int = 100) -> TeamListResponse:
        """Search teams by name or description."""
        logger.debug(f"Searching teams: {search_term}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            teams, total = self.team_repo.search(search_term, skip=skip, limit=limit)
            
            # Convert to responses
            team_responses = []
            for team in teams:
                member_count = self.team_repo.get_member_count(team.team_id)
                
                response_data = {
                    'team_id': team.team_id,
                    'team_name': team.team_name,
                    'description': team.description,
                    'updated_by': team.updated_by,
                    'updated_at': team.updated_at,
                    'member_count': member_count
                }
                
                # Add related data if available
                if hasattr(team, 'updater') and team.updater:
                    response_data['updated_by_name'] = team.updater.full_name
                
                team_responses.append(TeamResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return TeamListResponse(
                teams=team_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error searching teams: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_team(self, team_data: TeamCreate, request) -> TeamResponse:
        """Create a new team."""
        logger.info(f"Creating new team: {team_data.team_name}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Convert to dict and create
            team_dict = team_data.dict(exclude_none=True)
            team = self.team_repo.create(team_dict, updated_by=current_user_id)
            
            return self.get_team(team.team_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating team: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_team(self, team_id: int, update_data: TeamUpdate, request) -> TeamResponse:
        """Update an existing team."""
        logger.info(f"Updating team: {team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Get team
            team = self.team_repo.get_by_id(team_id)
            if not team:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found"
                )
            
            # Update team
            update_dict = update_data.dict(exclude_none=True)
            self.team_repo.update(team, update_dict, updated_by=current_user_id)
            
            return self.get_team(team_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating team {team_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_team(self, team_id: int, request) -> dict:
        """Delete a team."""
        logger.warning(f"Deleting team: {team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Check if team exists
            team = self.team_repo.get_by_id(team_id)
            if not team:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found"
                )
            
            # Delete team
            try:
                success = self.team_repo.delete(team_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Team not found"
                    )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            
            return {"message": "Team deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting team {team_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )