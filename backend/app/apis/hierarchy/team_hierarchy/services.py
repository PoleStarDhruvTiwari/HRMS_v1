import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from .repositories import TeamHierarchyRepository
from .schemas import (
    NewTeamHierarchyCreate,
    TeamHierarchyUpdate,
    TeamHierarchyResponse,
    TeamHierarchyListResponse,
    TeamChainResponse,
    ChildTeamsResponse,
    TeamTreeResponse,
    TeamHierarchyCreationResponse
)

logger = logging.getLogger(__name__)


class TeamHierarchyService(BaseService):
    """Service for team hierarchy business logic."""
    
    def __init__(self, hierarchy_repo: TeamHierarchyRepository, db: Session):
        super().__init__(db)
        self.hierarchy_repo = hierarchy_repo
        self.db = db
    
    def get_hierarchy_entries_for_team(self, child_team_id: int, request) -> List[TeamHierarchyResponse]:
        """Get ALL hierarchy entries for a child team."""
        logger.debug(f"Getting all hierarchy entries for team: {child_team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "team_hierarchy.view")
            
            entries = self.hierarchy_repo.get_by_child_team_id(child_team_id)
            if not entries:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No hierarchy entries found for team: {child_team_id}"
                )
            
            responses = []
            for entry in entries:
                response_data = {
                    "id": entry.id,
                    "child_team_id": entry.child_team_id,
                    "parent_team_id": entry.parent_team_id,
                    "depth_level": entry.depth_level,
                    "updated_by": entry.updated_by,
                    "updated_at": entry.updated_at,
                    "child_team_name": self._get_team_name(entry.child_team_id),
                    "parent_team_name": self._get_team_name(entry.parent_team_id) if entry.parent_team_id else None,
                    "updated_by_name": self._get_user_name(entry.updated_by) if entry.updated_by else None
                }
                responses.append(TeamHierarchyResponse(**response_data))
            
            return responses
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting hierarchy entries for team {child_team_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_all_hierarchies(self, request, skip: int = 0, limit: int = 100) -> TeamHierarchyListResponse:
        """Get all hierarchy entries with pagination."""
        logger.debug(f"Getting all team hierarchies (skip: {skip}, limit: {limit})")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "team_hierarchy.view")
            
            entries = self.hierarchy_repo.get_all(skip=skip, limit=limit)
            total = self.hierarchy_repo.get_count()
            
            responses = []
            for entry in entries:
                response_data = {
                    "id": entry.id,
                    "child_team_id": entry.child_team_id,
                    "parent_team_id": entry.parent_team_id,
                    "depth_level": entry.depth_level,
                    "updated_by": entry.updated_by,
                    "updated_at": entry.updated_at,
                    "child_team_name": self._get_team_name(entry.child_team_id),
                    "parent_team_name": self._get_team_name(entry.parent_team_id) if entry.parent_team_id else None,
                    "updated_by_name": self._get_user_name(entry.updated_by) if entry.updated_by else None
                }
                responses.append(TeamHierarchyResponse(**response_data))
            
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return TeamHierarchyListResponse(
                entries=responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting all team hierarchies: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_complete_hierarchy_for_team(self, create_data: NewTeamHierarchyCreate, request) -> TeamHierarchyCreationResponse:
        """
        Create complete hierarchy for a new team.
        """
        logger.info(f"Creating complete hierarchy for team: {create_data.child_team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "team_hierarchy.create")
            
            # Check if team already has any hierarchy entries
            existing_entries = self.hierarchy_repo.get_by_child_team_id(create_data.child_team_id)
            if existing_entries:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Team {create_data.child_team_id} already has hierarchy entries"
                )
            
            # Create complete hierarchy
            entries_created = self.hierarchy_repo.create_complete_hierarchy(
                child_team_id=create_data.child_team_id,
                first_parent_team_id=create_data.first_parent_team_id,
                updated_by=current_user_id
            )
            
            if not entries_created:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create hierarchy entries"
                )
            
            # Prepare responses
            entry_responses = []
            for entry in entries_created:
                response_data = {
                    "id": entry.id,
                    "child_team_id": entry.child_team_id,
                    "parent_team_id": entry.parent_team_id,
                    "depth_level": entry.depth_level,
                    "updated_by": entry.updated_by,
                    "updated_at": entry.updated_at,
                    "child_team_name": self._get_team_name(entry.child_team_id),
                    "parent_team_name": self._get_team_name(entry.parent_team_id) if entry.parent_team_id else None,
                    "updated_by_name": self._get_user_name(entry.updated_by) if entry.updated_by else None
                }
                entry_responses.append(TeamHierarchyResponse(**response_data))
            
            return TeamHierarchyCreationResponse(
                message=f"Created {len(entries_created)} hierarchy entries successfully",
                new_hierarchy_entries=entry_responses
            )
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating complete hierarchy for team: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_parent_relationship(self, child_team_id: int, update_data: TeamHierarchyUpdate, request) -> List[TeamHierarchyResponse]:
        """Update parent relationship for a team."""
        logger.info(f"Updating parent relationship for team: {child_team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "team_hierarchy.update")
            
            # Update parent relationship
            updated_entries = self.hierarchy_repo.update_parent_relationship(
                child_team_id=child_team_id,
                new_parent_team_id=update_data.parent_team_id,
                updated_by=current_user_id
            )
            
            # Prepare responses
            responses = []
            for entry in updated_entries:
                response_data = {
                    "id": entry.id,
                    "child_team_id": entry.child_team_id,
                    "parent_team_id": entry.parent_team_id,
                    "depth_level": entry.depth_level,
                    "updated_by": entry.updated_by,
                    "updated_at": entry.updated_at,
                    "child_team_name": self._get_team_name(entry.child_team_id),
                    "parent_team_name": self._get_team_name(entry.parent_team_id) if entry.parent_team_id else None,
                    "updated_by_name": self._get_user_name(entry.updated_by) if entry.updated_by else None
                }
                responses.append(TeamHierarchyResponse(**response_data))
            
            return responses
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating team parent relationship: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_hierarchy_entries(self, child_team_id: int, request) -> dict:
        """Delete ALL hierarchy entries for a team."""
        logger.warning(f"Deleting all hierarchy entries for team: {child_team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "team_hierarchy.delete")
            
            success = self.hierarchy_repo.delete_by_child_team_id(child_team_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No hierarchy entries found for team: {child_team_id}"
                )
            
            return {"message": f"All hierarchy entries deleted successfully for team: {child_team_id}"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting team hierarchy entries: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_team_chain(self, child_team_id: int, request) -> TeamChainResponse:
        """Get complete parent chain for a team."""
        logger.debug(f"Getting team chain for team: {child_team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "team_hierarchy.view")
            
            entries = self.hierarchy_repo.get_team_chain(child_team_id)
            
            if not entries:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No hierarchy entries found for team: {child_team_id}"
                )
            
            chain_data = []
            for entry in entries:
                chain_data.append({
                    "parent_team_id": entry.parent_team_id,
                    "child_team_id": entry.child_team_id,
                    "depth_level": entry.depth_level,
                    "parent_team_name": self._get_team_name(entry.parent_team_id) if entry.parent_team_id else None,
                    "child_team_name": self._get_team_name(entry.child_team_id)
                })
            
            return TeamChainResponse(
                child_team_id=child_team_id,
                chain=chain_data,
                total_levels=len(chain_data)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting team chain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_child_teams(self, parent_team_id: int, include_indirect: bool, request) -> ChildTeamsResponse:
        """Get teams that report to a specific parent team."""
        logger.debug(f"Getting child teams for parent: {parent_team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "team_hierarchy.view")
            
            child_entries = self.hierarchy_repo.get_child_teams(parent_team_id, include_indirect)
            
            child_teams_data = []
            for entry in child_entries:
                child_teams_data.append({
                    "child_team_id": entry.child_team_id,
                    "parent_team_id": entry.parent_team_id,
                    "depth_level": entry.depth_level,
                    "child_team_name": self._get_team_name(entry.child_team_id),
                    "parent_team_name": self._get_team_name(entry.parent_team_id) if entry.parent_team_id else None
                })
            
            return ChildTeamsResponse(
                parent_team_id=parent_team_id,
                child_teams=child_teams_data,
                total_count=len(child_teams_data),
                include_indirect=include_indirect
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting child teams: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_team_tree(self, top_team_id: Optional[int], request) -> Dict[str, Any]:
        """Get organizational tree of teams."""
        logger.debug(f"Getting team tree for top team: {top_team_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "team_hierarchy.view")
            
            tree_data = self.hierarchy_repo.get_team_tree(top_team_id)
            return tree_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting team tree: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _get_team_name(self, team_id: int) -> Optional[str]:
        """Get team name by ID."""
        try:
            # Import Team model from organization.teams
            from app.apis.organization.teams.models import Team
            
            team = self.db.query(Team).filter(Team.team_id == team_id).first()
            if team:
                return team.team_name
            return f"Team {team_id}"
        except Exception as e:
            logger.error(f"Error getting team name for {team_id}: {str(e)}")
            return f"Team {team_id}"
    
    def _get_user_name(self, user_id: int) -> Optional[str]:
        """Get user name by ID from ExistingUser model."""
        try:
            from app.apis.auth.models import ExistingUser
            
            user = self.db.query(ExistingUser).filter(ExistingUser.user_id == user_id).first()
            if user and user.full_name:
                return user.full_name
            return f"User {user_id}"
        except Exception as e:
            logger.error(f"Error getting user name for {user_id}: {str(e)}")
            return f"User {user_id}"