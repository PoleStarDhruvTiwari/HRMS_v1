# app/apis/organization/teams/repositories.py
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func

from .models import Team

logger = logging.getLogger(__name__)


class TeamRepository:
    """Repository for Team database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by ID."""
        logger.debug(f"Fetching team by ID: {team_id}")
        try:
            team = self.db.query(Team).filter(Team.team_id == team_id).first()
            return team
        except Exception as e:
            logger.error(f"Error fetching team by ID {team_id}: {str(e)}")
            raise
    
    def get_by_name(self, team_name: str) -> Optional[Team]:
        """Get team by name."""
        logger.debug(f"Fetching team by name: {team_name}")
        try:
            team = self.db.query(Team).filter(Team.team_name == team_name.title()).first()
            return team
        except Exception as e:
            logger.error(f"Error fetching team by name {team_name}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Team]:
        """Get all teams with pagination."""
        logger.debug(f"Fetching all teams (skip: {skip}, limit: {limit})")
        try:
            teams = self.db.query(Team).offset(skip).limit(limit).all()
            return teams
        except Exception as e:
            logger.error(f"Error fetching all teams: {str(e)}")
            raise
    
    def create(self, team_data: Dict[str, Any], updated_by: int) -> Team:
        """Create a new team."""
        logger.info(f"Creating new team: {team_data.get('team_name')}")
        
        try:
            # Check if team already exists
            existing = self.get_by_name(team_data['team_name'])
            if existing:
                raise ValueError(f"Team already exists: {team_data['team_name']}")
            
            # Create team
            team = Team(**team_data)
            team.updated_by = updated_by
            
            self.db.add(team)
            self.db.commit()
            self.db.refresh(team)
            
            logger.info(f"Team created successfully: {team.team_id}")
            return team
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating team: {str(e)}")
            raise
    
    def update(self, team: Team, update_data: Dict[str, Any], updated_by: int) -> Team:
        """Update an existing team."""
        logger.debug(f"Updating team: {team.team_id}")
        
        try:
            # Check for duplicate team_name if being changed
            if 'team_name' in update_data and update_data['team_name'] != team.team_name:
                existing = self.get_by_name(update_data['team_name'])
                if existing and existing.team_id != team.team_id:
                    raise ValueError(f"Team name already exists: {update_data['team_name']}")
            
            # Update fields
            for key, value in update_data.items():
                if value is not None and hasattr(team, key):
                    setattr(team, key, value)
            
            # Update metadata
            team.updated_by = updated_by
            
            self.db.commit()
            self.db.refresh(team)
            
            logger.debug(f"Team updated successfully: {team.team_id}")
            return team
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating team {team.team_id}: {str(e)}")
            raise
    
    def delete(self, team_id: int) -> bool:
        """Delete a team."""
        logger.warning(f"Deleting team: {team_id}")
        
        try:
            team = self.get_by_id(team_id)
            if not team:
                return False
            
            # Check if team has members
            from app.apis.auth.models import ExistingUser
            member_count = self.db.query(ExistingUser).filter(ExistingUser.team_id == team_id).count()
            if member_count > 0:
                raise ValueError(f"Cannot delete team {team.team_name}. It has {member_count} member(s).")
            
            self.db.delete(team)
            self.db.commit()
            
            logger.warning(f"Team deleted successfully: {team_id}")
            return True
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting team {team_id}: {str(e)}")
            raise
    
    def search(self, search_term: str = None, skip: int = 0, limit: int = 100) -> Tuple[List[Team], int]:
        """Search teams by name or description."""
        logger.debug(f"Searching teams: {search_term}")
        
        try:
            query = self.db.query(Team)
            
            if search_term:
                search = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Team.team_name.ilike(search),
                        Team.description.ilike(search)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            teams = query.offset(skip).limit(limit).all()
            
            return teams, total
            
        except Exception as e:
            logger.error(f"Error searching teams: {str(e)}")
            raise
    
    def get_member_count(self, team_id: int) -> int:
        """Get number of users in a team."""
        logger.debug(f"Getting member count for team: {team_id}")
        
        try:
            from app.apis.auth.models import ExistingUser
            count = self.db.query(func.count(ExistingUser.user_id)).filter(
                ExistingUser.team_id == team_id
            ).scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Error getting member count for team {team_id}: {str(e)}")
            return 0
    
    def get_teams_with_member_counts(self, skip: int = 0, limit: int = 100) -> List[Tuple[Team, int]]:
        """Get teams with their member counts."""
        logger.debug(f"Getting teams with member counts")
        
        try:
            # Get all teams
            teams = self.get_all(skip=skip, limit=limit)
            
            # Get member counts for each team
            teams_with_counts = []
            for team in teams:
                count = self.get_member_count(team.team_id)
                teams_with_counts.append((team, count))
            
            return teams_with_counts
            
        except Exception as e:
            logger.error(f"Error getting teams with member counts: {str(e)}")
            raise
    
    def get_count(self) -> int:
        """Get total team count."""
        logger.debug("Getting team count")
        try:
            count = self.db.query(func.count(Team.team_id)).scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting team count: {str(e)}")
            raise