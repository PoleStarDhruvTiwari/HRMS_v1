# app/apis/organization/designations/repositories.py
import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func

from .models import Designation

logger = logging.getLogger(__name__)


class DesignationRepository:
    """Repository for Designation database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, designation_id: int) -> Optional[Designation]:
        """Get designation by ID."""
        logger.debug(f"Fetching designation by ID: {designation_id}")
        try:
            designation = self.db.query(Designation).filter(
                Designation.designation_id == designation_id
            ).first()
            return designation
        except Exception as e:
            logger.error(f"Error fetching designation by ID {designation_id}: {str(e)}")
            raise
    
    def get_by_code(self, designation_code: str) -> Optional[Designation]:
        """Get designation by code."""
        logger.debug(f"Fetching designation by code: {designation_code}")
        try:
            designation = self.db.query(Designation).filter(
                Designation.designation_code == designation_code.upper()
            ).first()
            return designation
        except Exception as e:
            logger.error(f"Error fetching designation by code {designation_code}: {str(e)}")
            raise
    
    def get_by_name(self, designation_name: str) -> Optional[Designation]:
        """Get designation by name."""
        logger.debug(f"Fetching designation by name: {designation_name}")
        try:
            designation = self.db.query(Designation).filter(
                Designation.designation_name == designation_name.title()
            ).first()
            return designation
        except Exception as e:
            logger.error(f"Error fetching designation by name {designation_name}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Designation]:
        """Get all designations with pagination."""
        logger.debug(f"Fetching all designations (skip: {skip}, limit: {limit})")
        try:
            designations = self.db.query(Designation).offset(skip).limit(limit).all()
            return designations
        except Exception as e:
            logger.error(f"Error fetching all designations: {str(e)}")
            raise
    
    def create(self, designation_data: Dict[str, Any], updated_by: int) -> Designation:
        """Create a new designation."""
        logger.info(f"Creating new designation: {designation_data.get('designation_code')}")
        
        try:
            # Check if designation already exists by code
            existing_by_code = self.get_by_code(designation_data['designation_code'])
            if existing_by_code:
                raise ValueError(f"Designation code already exists: {designation_data['designation_code']}")
            
            # Check if designation already exists by name
            existing_by_name = self.get_by_name(designation_data['designation_name'])
            if existing_by_name:
                raise ValueError(f"Designation name already exists: {designation_data['designation_name']}")
            
            # Create designation
            designation = Designation(**designation_data)
            designation.updated_by = updated_by
            
            self.db.add(designation)
            self.db.commit()
            self.db.refresh(designation)
            
            logger.info(f"Designation created successfully: {designation.designation_id}")
            return designation
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating designation: {str(e)}")
            raise
    
    def update(self, designation: Designation, update_data: Dict[str, Any], updated_by: int) -> Designation:
        """Update an existing designation."""
        logger.debug(f"Updating designation: {designation.designation_id}")
        
        try:
            # Check for duplicate designation_code if being changed
            if 'designation_code' in update_data and update_data['designation_code'] != designation.designation_code:
                existing_by_code = self.get_by_code(update_data['designation_code'])
                if existing_by_code and existing_by_code.designation_id != designation.designation_id:
                    raise ValueError(f"Designation code already exists: {update_data['designation_code']}")
            
            # Check for duplicate designation_name if being changed
            if 'designation_name' in update_data and update_data['designation_name'] != designation.designation_name:
                existing_by_name = self.get_by_name(update_data['designation_name'])
                if existing_by_name and existing_by_name.designation_id != designation.designation_id:
                    raise ValueError(f"Designation name already exists: {update_data['designation_name']}")
            
            # Update fields
            for key, value in update_data.items():
                if value is not None and hasattr(designation, key):
                    setattr(designation, key, value)
            
            # Update metadata
            designation.updated_by = updated_by
            
            self.db.commit()
            self.db.refresh(designation)
            
            logger.debug(f"Designation updated successfully: {designation.designation_id}")
            return designation
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating designation {designation.designation_id}: {str(e)}")
            raise
    
    def delete(self, designation_id: int) -> bool:
        """Delete a designation."""
        logger.warning(f"Deleting designation: {designation_id}")
        
        try:
            designation = self.get_by_id(designation_id)
            if not designation:
                return False
            
            # Check if designation has users
            from app.apis.auth.models import ExistingUser
            user_count = self.db.query(ExistingUser).filter(
                ExistingUser.designation_id == designation_id
            ).count()
            
            if user_count > 0:
                raise ValueError(f"Cannot delete designation {designation.designation_name}. It has {user_count} user(s).")
            
            self.db.delete(designation)
            self.db.commit()
            
            logger.warning(f"Designation deleted successfully: {designation_id}")
            return True
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting designation {designation_id}: {str(e)}")
            raise
    
    def search(self, search_term: str = None, skip: int = 0, limit: int = 100) -> Tuple[List[Designation], int]:
        """Search designations by code or name."""
        logger.debug(f"Searching designations: {search_term}")
        
        try:
            query = self.db.query(Designation)
            
            if search_term:
                search = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Designation.designation_code.ilike(search),
                        Designation.designation_name.ilike(search)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            designations = query.offset(skip).limit(limit).all()
            
            return designations, total
            
        except Exception as e:
            logger.error(f"Error searching designations: {str(e)}")
            raise
    
    def get_user_count(self, designation_id: int) -> int:
        """Get number of users with a designation."""
        logger.debug(f"Getting user count for designation: {designation_id}")
        
        try:
            from app.apis.auth.models import ExistingUser
            count = self.db.query(func.count(ExistingUser.user_id)).filter(
                ExistingUser.designation_id == designation_id
            ).scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Error getting user count for designation {designation_id}: {str(e)}")
            return 0
    
    def get_designations_with_user_counts(self, skip: int = 0, limit: int = 100) -> List[Tuple[Designation, int]]:
        """Get designations with their user counts."""
        logger.debug(f"Getting designations with user counts")
        
        try:
            # Get all designations
            designations = self.get_all(skip=skip, limit=limit)
            
            # Get user counts for each designation
            designations_with_counts = []
            for designation in designations:
                count = self.get_user_count(designation.designation_id)
                designations_with_counts.append((designation, count))
            
            return designations_with_counts
            
        except Exception as e:
            logger.error(f"Error getting designations with user counts: {str(e)}")
            raise
    
    def get_count(self) -> int:
        """Get total designation count."""
        logger.debug("Getting designation count")
        try:
            count = self.db.query(func.count(Designation.designation_id)).scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting designation count: {str(e)}")
            raise