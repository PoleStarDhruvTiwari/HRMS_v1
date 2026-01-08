import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from .models import TeamHierarchy

logger = logging.getLogger(__name__)


class TeamHierarchyRepository:
    """Repository for Team Hierarchy database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, hierarchy_id: int) -> Optional[TeamHierarchy]:
        """Get hierarchy entry by ID."""
        try:
            return self.db.query(TeamHierarchy).filter(
                TeamHierarchy.id == hierarchy_id
            ).first()
        except Exception as e:
            logger.error(f"Error fetching team hierarchy {hierarchy_id}: {str(e)}")
            raise
    
    def get_by_child_team_id(self, child_team_id: int) -> List[TeamHierarchy]:
        """Get ALL hierarchy entries for a child team."""
        try:
            entries = self.db.query(TeamHierarchy).filter(
                TeamHierarchy.child_team_id == child_team_id
            ).order_by(TeamHierarchy.depth_level).all()
            return entries
        except Exception as e:
            logger.error(f"Error fetching hierarchy for child team {child_team_id}: {str(e)}")
            raise
    
    def get_direct_parent(self, child_team_id: int) -> Optional[TeamHierarchy]:
        """Get direct parent relationship for a team (depth_level = 1)."""
        try:
            entry = self.db.query(TeamHierarchy).filter(
                TeamHierarchy.child_team_id == child_team_id,
                TeamHierarchy.depth_level == 1
            ).first()
            return entry
        except Exception as e:
            logger.error(f"Error fetching direct parent for team {child_team_id}: {str(e)}")
            raise
    
    def get_team_chain(self, child_team_id: int) -> List[TeamHierarchy]:
        """Get complete parent chain for a team (all ancestors)."""
        try:
            # Get all hierarchy entries for this child team
            all_entries = self.get_by_child_team_id(child_team_id)
            
            # Sort by depth level
            all_entries.sort(key=lambda x: x.depth_level)
            return all_entries
            
        except Exception as e:
            logger.error(f"Error fetching team chain for team {child_team_id}: {str(e)}")
            raise
    
    def create_entry(self, parent_team_id: Optional[int], child_team_id: int, depth_level: int, updated_by: int) -> TeamHierarchy:
        """Create a single hierarchy entry."""
        try:
            # Check if same entry already exists
            existing = self.db.query(TeamHierarchy).filter(
                TeamHierarchy.parent_team_id == parent_team_id,
                TeamHierarchy.child_team_id == child_team_id,
                TeamHierarchy.depth_level == depth_level
            ).first()
            
            if existing:
                return existing
            
            entry = TeamHierarchy(
                parent_team_id=parent_team_id,
                child_team_id=child_team_id,
                depth_level=depth_level,
                updated_by=updated_by
            )
            
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            
            logger.info(f"Created team hierarchy: child {child_team_id} under parent {parent_team_id} at depth {depth_level}")
            return entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating team hierarchy entry: {str(e)}")
            raise
    
    def create_complete_hierarchy(self, child_team_id: int, first_parent_team_id: Optional[int], updated_by: int) -> List[TeamHierarchy]:
        """
        Create complete hierarchy for a new team.
        
        Copies the entire parent chain of the first_parent_team_id,
        but increases all depth levels by 1 for the new team.
        """
        try:
            entries_created = []
            
            if first_parent_team_id:
                # Step 1: Create direct parent relationship (depth_level 1)
                direct_entry = self.create_entry(
                    parent_team_id=first_parent_team_id,
                    child_team_id=child_team_id,
                    depth_level=1,
                    updated_by=updated_by
                )
                entries_created.append(direct_entry)
                
                # Step 2: Get ALL parent entries of the first parent team
                parent_team_entries = self.get_by_child_team_id(first_parent_team_id)
                
                # Step 3: For each parent entry, create a corresponding entry for new team
                # with depth_level = parent_entry.depth_level + 1
                for parent_entry in parent_team_entries:
                    if parent_entry.parent_team_id:  # Skip if parent doesn't have parent
                        new_entry = self.create_entry(
                            parent_team_id=parent_entry.parent_team_id,
                            child_team_id=child_team_id,
                            depth_level=parent_entry.depth_level + 1,  # Increase depth by 1
                            updated_by=updated_by
                        )
                        entries_created.append(new_entry)
                
                # Sort by depth level
                entries_created.sort(key=lambda x: x.depth_level)
                
            else:
                # Team has no parent (top-level)
                top_entry = self.create_entry(
                    parent_team_id=None,
                    child_team_id=child_team_id,
                    depth_level=0,
                    updated_by=updated_by
                )
                entries_created.append(top_entry)
            
            self.db.commit()
            logger.info(f"Created {len(entries_created)} hierarchy entries for team {child_team_id}")
            return entries_created
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating complete team hierarchy: {str(e)}")
            raise
    
    def update_parent_relationship(self, child_team_id: int, new_parent_team_id: Optional[int], updated_by: int) -> List[TeamHierarchy]:
        """Update parent relationship for a team (recreates entire chain)."""
        try:
            # Step 1: Delete all existing hierarchy entries for this child team
            existing_entries = self.get_by_child_team_id(child_team_id)
            for entry in existing_entries:
                self.db.delete(entry)
            
            # Step 2: Create new complete hierarchy
            new_entries = self.create_complete_hierarchy(
                child_team_id=child_team_id,
                first_parent_team_id=new_parent_team_id,
                updated_by=updated_by
            )
            
            self.db.commit()
            logger.info(f"Updated parent relationship for team {child_team_id} to parent {new_parent_team_id}")
            return new_entries
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating team parent relationship: {str(e)}")
            raise
    
    def delete_by_child_team_id(self, child_team_id: int) -> bool:
        """Delete ALL hierarchy entries for a child team."""
        try:
            entries = self.get_by_child_team_id(child_team_id)
            if not entries:
                return False
            
            for entry in entries:
                self.db.delete(entry)
            
            self.db.commit()
            logger.info(f"Deleted {len(entries)} hierarchy entries for team {child_team_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting team hierarchy entries for team {child_team_id}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[TeamHierarchy]:
        """Get all hierarchy entries with pagination."""
        try:
            entries = self.db.query(TeamHierarchy).order_by(
                TeamHierarchy.child_team_id,
                TeamHierarchy.depth_level
            ).offset(skip).limit(limit).all()
            return entries
        except Exception as e:
            logger.error(f"Error fetching all team hierarchy entries: {str(e)}")
            raise
    
    def get_count(self) -> int:
        """Get total hierarchy entry count."""
        try:
            count = self.db.query(func.count(TeamHierarchy.id)).scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting team hierarchy count: {str(e)}")
            raise
    
    def get_child_teams(self, parent_team_id: int, include_indirect: bool = False) -> List[TeamHierarchy]:
        """Get teams that report to a specific parent team."""
        try:
            if include_indirect:
                # Get all child teams (direct and indirect)
                entries = self.db.query(TeamHierarchy).filter(
                    TeamHierarchy.parent_team_id == parent_team_id
                ).all()
            else:
                # Get only direct child teams (depth_level = 1)
                entries = self.db.query(TeamHierarchy).filter(
                    TeamHierarchy.parent_team_id == parent_team_id,
                    TeamHierarchy.depth_level == 1
                ).all()
            
            return entries
        except Exception as e:
            logger.error(f"Error fetching child teams for parent {parent_team_id}: {str(e)}")
            raise
    
    def get_team_tree(self, top_team_id: Optional[int] = None) -> Dict[str, Any]:
        """Get organizational tree of teams."""
        try:
            if top_team_id:
                # Get tree starting from specific team
                team_chain = self.get_team_chain(top_team_id)
                
                # Build tree structure
                tree = {
                    "team_id": top_team_id,
                    "depth": 0,
                    "children": []
                }
                
                # Get direct children
                direct_children = self.get_child_teams(top_team_id, include_indirect=False)
                for child in direct_children:
                    child_tree = self.get_team_tree(child.child_team_id)
                    tree["children"].append(child_tree)
                
                return tree
            else:
                # Get all top-level teams (no parent)
                top_level_entries = self.db.query(TeamHierarchy).filter(
                    TeamHierarchy.parent_team_id.is_(None)
                ).all()
                
                top_teams = []
                for entry in top_level_entries:
                    team_tree = self.get_team_tree(entry.child_team_id)
                    top_teams.append(team_tree)
                
                return {"teams": top_teams}
                
        except Exception as e:
            logger.error(f"Error getting team tree: {str(e)}")
            raise