# app/apis/organization/shifts/repositories.py
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func

from .models import Shift

logger = logging.getLogger(__name__)


class ShiftRepository:
    """Repository for Shift database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, shift_id: int) -> Optional[Shift]:
        """Get shift by ID."""
        logger.debug(f"Fetching shift by ID: {shift_id}")
        try:
            shift = self.db.query(Shift).filter(Shift.shift_id == shift_id).first()
            return shift
        except Exception as e:
            logger.error(f"Error fetching shift by ID {shift_id}: {str(e)}")
            raise
    
    def get_by_name(self, shift_name: str) -> Optional[Shift]:
        """Get shift by name."""
        logger.debug(f"Fetching shift by name: {shift_name}")
        try:
            shift = self.db.query(Shift).filter(Shift.shift_name == shift_name.upper()).first()
            return shift
        except Exception as e:
            logger.error(f"Error fetching shift by name {shift_name}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Shift]:
        """Get all shifts with pagination."""
        logger.debug(f"Fetching all shifts (skip: {skip}, limit: {limit})")
        try:
            shifts = self.db.query(Shift).offset(skip).limit(limit).all()
            return shifts
        except Exception as e:
            logger.error(f"Error fetching all shifts: {str(e)}")
            raise
    
    def create(self, shift_data: Dict[str, Any], updated_by: int) -> Shift:
        """Create a new shift."""
        logger.info(f"Creating new shift: {shift_data.get('shift_name')}")
        
        try:
            # Check if shift already exists
            existing = self.get_by_name(shift_data['shift_name'])
            if existing:
                raise ValueError(f"Shift already exists: {shift_data['shift_name']}")
            
            # Create shift
            shift = Shift(**shift_data)
            shift.updated_by = updated_by
            
            self.db.add(shift)
            self.db.commit()
            self.db.refresh(shift)
            
            logger.info(f"Shift created successfully: {shift.shift_id}")
            return shift
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating shift: {str(e)}")
            raise
    
    def update(self, shift: Shift, update_data: Dict[str, Any], updated_by: int) -> Shift:
        """Update an existing shift."""
        logger.debug(f"Updating shift: {shift.shift_id}")
        
        try:
            # Check for duplicate shift_name if being changed
            if 'shift_name' in update_data and update_data['shift_name'] != shift.shift_name:
                existing = self.get_by_name(update_data['shift_name'])
                if existing and existing.shift_id != shift.shift_id:
                    raise ValueError(f"Shift name already exists: {update_data['shift_name']}")
            
            # Update fields
            for key, value in update_data.items():
                if value is not None and hasattr(shift, key):
                    setattr(shift, key, value)
            
            # Update metadata
            shift.updated_by = updated_by
            
            self.db.commit()
            self.db.refresh(shift)
            
            logger.debug(f"Shift updated successfully: {shift.shift_id}")
            return shift
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating shift {shift.shift_id}: {str(e)}")
            raise
    
    def delete(self, shift_id: int) -> bool:
        """Delete a shift."""
        logger.warning(f"Deleting shift: {shift_id}")
        
        try:
            shift = self.get_by_id(shift_id)
            if not shift:
                return False
            
            self.db.delete(shift)
            self.db.commit()
            
            logger.warning(f"Shift deleted successfully: {shift_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting shift {shift_id}: {str(e)}")
            raise
    
    def search(self, search_term: str = None, skip: int = 0, limit: int = 100) -> Tuple[List[Shift], int]:
        """Search shifts by name."""
        logger.debug(f"Searching shifts: {search_term}")
        
        try:
            query = self.db.query(Shift)
            
            if search_term:
                search = f"%{search_term}%"
                query = query.filter(Shift.shift_name.ilike(search))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            shifts = query.offset(skip).limit(limit).all()
            
            return shifts, total
            
        except Exception as e:
            logger.error(f"Error searching shifts: {str(e)}")
            raise
    
    def get_shift_duration(self, shift_id: int) -> Optional[float]:
        """Calculate shift duration in hours."""
        logger.debug(f"Calculating duration for shift: {shift_id}")
        
        try:
            shift = self.get_by_id(shift_id)
            if not shift or not shift.start_time or not shift.end_time:
                return None
            
            # Calculate duration in hours
            start_dt = datetime.combine(datetime.today(), shift.start_time)
            end_dt = datetime.combine(datetime.today(), shift.end_time)
            
            # Handle overnight shifts
            if end_dt <= start_dt:
                end_dt = datetime.combine(datetime.today(), shift.end_time)
                end_dt = end_dt.replace(day=end_dt.day + 1)
            
            duration = (end_dt - start_dt).total_seconds() / 3600
            return duration
            
        except Exception as e:
            logger.error(f"Error calculating shift duration: {str(e)}")
            return None
    
    def get_default_shifts(self) -> List[Dict[str, Any]]:
        """Get default shift configurations."""
        return [
            {
                "shift_name": "MORNING",
                "start_time": time(9, 0, 0),
                "end_time": time(17, 0, 0)
            },
            {
                "shift_name": "NIGHT",
                "start_time": time(17, 0, 0),
                "end_time": time(1, 0, 0)
            },
            {
                "shift_name": "GENERAL",
                "start_time": time(8, 0, 0),
                "end_time": time(16, 0, 0)
            }
        ]
    
    def get_count(self) -> int:
        """Get total shift count."""
        logger.debug("Getting shift count")
        try:
            count = self.db.query(func.count(Shift.shift_id)).scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting shift count: {str(e)}")
            raise