# app/apis/organization/offices/repositories.py
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func, text
import math

from .models import Office

logger = logging.getLogger(__name__)


class OfficeRepository:
    """Repository for Office database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, office_id: int) -> Optional[Office]:
        """Get office by ID."""
        logger.debug(f"Fetching office by ID: {office_id}")
        try:
            office = self.db.query(Office).filter(Office.office_id == office_id).first()
            return office
        except Exception as e:
            logger.error(f"Error fetching office by ID {office_id}: {str(e)}")
            raise
    
    def get_by_name(self, office_name: str) -> Optional[Office]:
        """Get office by name."""
        logger.debug(f"Fetching office by name: {office_name}")
        try:
            office = self.db.query(Office).filter(Office.office_name == office_name).first()
            return office
        except Exception as e:
            logger.error(f"Error fetching office by name {office_name}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Office]:
        """Get all offices with pagination."""
        logger.debug(f"Fetching all offices (skip: {skip}, limit: {limit})")
        try:
            offices = self.db.query(Office).offset(skip).limit(limit).all()
            return offices
        except Exception as e:
            logger.error(f"Error fetching all offices: {str(e)}")
            raise
    
    def create(self, office_data: Dict[str, Any], updated_by: int) -> Office:
        """Create a new office."""
        logger.info(f"Creating new office: {office_data.get('office_name')}")
        
        try:
            # Check if office already exists
            existing = self.get_by_name(office_data['office_name'])
            if existing:
                raise ValueError(f"Office already exists: {office_data['office_name']}")
            
            # Create office
            office = Office(**office_data)
            office.updated_by = updated_by
            
            self.db.add(office)
            self.db.commit()
            self.db.refresh(office)
            
            logger.info(f"Office created successfully: {office.office_id}")
            return office
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating office: {str(e)}")
            raise
    
    def update(self, office: Office, update_data: Dict[str, Any], updated_by: int) -> Office:
        """Update an existing office."""
        logger.debug(f"Updating office: {office.office_id}")
        
        try:
            # Check for duplicate office_name if being changed
            if 'office_name' in update_data and update_data['office_name'] != office.office_name:
                existing = self.get_by_name(update_data['office_name'])
                if existing and existing.office_id != office.office_id:
                    raise ValueError(f"Office name already exists: {update_data['office_name']}")
            
            # Update fields
            for key, value in update_data.items():
                if value is not None and hasattr(office, key):
                    setattr(office, key, value)
            
            # Update metadata
            office.updated_by = updated_by
            
            self.db.commit()
            self.db.refresh(office)
            
            logger.debug(f"Office updated successfully: {office.office_id}")
            return office
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating office {office.office_id}: {str(e)}")
            raise
    
    def delete(self, office_id: int) -> bool:
        """Delete an office."""
        logger.warning(f"Deleting office: {office_id}")
        
        try:
            office = self.get_by_id(office_id)
            if not office:
                return False
            
            self.db.delete(office)
            self.db.commit()
            
            logger.warning(f"Office deleted successfully: {office_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting office {office_id}: {str(e)}")
            raise
    
    def search(self, search_term: str = None, skip: int = 0, limit: int = 100) -> Tuple[List[Office], int]:
        """Search offices by name."""
        logger.debug(f"Searching offices: {search_term}")
        
        try:
            query = self.db.query(Office)
            
            if search_term:
                search = f"%{search_term}%"
                query = query.filter(Office.office_name.ilike(search))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offices = query.offset(skip).limit(limit).all()
            
            return offices, total
            
        except Exception as e:
            logger.error(f"Error searching offices: {str(e)}")
            raise
    
    def get_nearby_offices(self, latitude: Decimal, longitude: Decimal, radius_km: int = 10, limit: int = 10) -> List[Tuple[Office, float]]:
        """Get offices within a radius (using Haversine formula)."""
        logger.debug(f"Finding offices near {latitude}, {longitude} within {radius_km}km")
        
        try:
            # Haversine formula SQL
            haversine_sql = """
                6371 * acos(
                    cos(radians(:lat)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(:lon)) + 
                    sin(radians(:lat)) * sin(radians(latitude))
                )
            """
            
            # Query with distance calculation
            query = self.db.query(
                Office,
                text(haversine_sql).label('distance')
            ).filter(
                text(f"{haversine_sql} <= :radius")
            ).params(
                lat=float(latitude),
                lon=float(longitude),
                radius=radius_km
            ).order_by('distance').limit(limit)
            
            results = query.all()
            
            # Format results
            offices_with_distance = []
            for office, distance in results:
                offices_with_distance.append((office, float(distance)))
            
            logger.debug(f"Found {len(offices_with_distance)} nearby offices")
            return offices_with_distance
            
        except Exception as e:
            logger.error(f"Error finding nearby offices: {str(e)}")
            # Fallback to simple distance calculation
            return self._fallback_nearby_offices(latitude, longitude, radius_km, limit)
    
    def _fallback_nearby_offices(self, latitude: Decimal, longitude: Decimal, radius_km: int, limit: int) -> List[Tuple[Office, float]]:
        """Fallback method for nearby offices calculation."""
        try:
            all_offices = self.db.query(Office).all()
            nearby_offices = []
            
            lat1 = float(latitude)
            lon1 = float(longitude)
            
            for office in all_offices:
                lat2 = float(office.latitude)
                lon2 = float(office.longitude)
                
                # Calculate distance using simple approximation
                distance = self._calculate_distance(lat1, lon1, lat2, lon2)
                
                if distance <= radius_km:
                    nearby_offices.append((office, distance))
            
            # Sort by distance and limit
            nearby_offices.sort(key=lambda x: x[1])
            return nearby_offices[:limit]
            
        except Exception as e:
            logger.error(f"Error in fallback nearby offices: {str(e)}")
            return []
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in km."""
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        radius = 6371  # Earth's radius in km
        return c * radius
    
    def get_count(self) -> int:
        """Get total office count."""
        logger.debug("Getting office count")
        try:
            count = self.db.query(func.count(Office.office_id)).scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting office count: {str(e)}")
            raise