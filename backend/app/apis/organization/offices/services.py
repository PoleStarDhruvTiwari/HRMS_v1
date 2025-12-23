# app/apis/organization/offices/services.py
import logging
from typing import List, Optional
from decimal import Decimal
from fastapi import HTTPException, status

from app.core.security import security_service
from .repositories import OfficeRepository
from .schemas import OfficeCreate, OfficeUpdate, OfficeResponse, OfficeListResponse, NearbyOfficeRequest, NearbyOfficeResponse

logger = logging.getLogger(__name__)


class OfficeService:
    """Service for office business logic."""
    
    def __init__(self, office_repo: OfficeRepository):
        self.office_repo = office_repo
    
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
    
    def get_office(self, office_id: int, request) -> OfficeResponse:
        """Get office by ID."""
        logger.debug(f"Getting office: {office_id}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            office = self.office_repo.get_by_id(office_id)
            if not office:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Office not found"
                )
            
            # Convert to response
            response_data = {
                'office_id': office.office_id,
                'office_name': office.office_name,
                'latitude': office.latitude,
                'longitude': office.longitude,
                'updated_by': office.updated_by,
                'updated_at': office.updated_at,
            }
            
            # Add related data if available
            if hasattr(office, 'updater') and office.updater:
                response_data['updated_by_name'] = office.updater.full_name
            
            return OfficeResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting office {office_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_offices(self, request, skip: int = 0, limit: int = 100) -> OfficeListResponse:
        """Get all offices with pagination."""
        logger.debug(f"Getting offices (skip: {skip}, limit: {limit})")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            offices = self.office_repo.get_all(skip=skip, limit=limit)
            total = self.office_repo.get_count()
            
            # Convert to responses
            office_responses = []
            for office in offices:
                response_data = {
                    'office_id': office.office_id,
                    'office_name': office.office_name,
                    'latitude': office.latitude,
                    'longitude': office.longitude,
                    'updated_by': office.updated_by,
                    'updated_at': office.updated_at,
                }
                
                # Add related data if available
                if hasattr(office, 'updater') and office.updater:
                    response_data['updated_by_name'] = office.updater.full_name
                
                office_responses.append(OfficeResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return OfficeListResponse(
                offices=office_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting offices: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def search_offices(self, search_term: str, request, skip: int = 0, limit: int = 100) -> OfficeListResponse:
        """Search offices by name."""
        logger.debug(f"Searching offices: {search_term}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            offices, total = self.office_repo.search(search_term, skip=skip, limit=limit)
            
            # Convert to responses
            office_responses = []
            for office in offices:
                response_data = {
                    'office_id': office.office_id,
                    'office_name': office.office_name,
                    'latitude': office.latitude,
                    'longitude': office.longitude,
                    'updated_by': office.updated_by,
                    'updated_at': office.updated_at,
                }
                
                # Add related data if available
                if hasattr(office, 'updater') and office.updater:
                    response_data['updated_by_name'] = office.updater.full_name
                
                office_responses.append(OfficeResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return OfficeListResponse(
                offices=office_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error searching offices: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_office(self, office_data: OfficeCreate, request) -> OfficeResponse:
        """Create a new office."""
        logger.info(f"Creating new office: {office_data.office_name}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Convert to dict and create
            office_dict = office_data.dict()
            office = self.office_repo.create(office_dict, updated_by=current_user_id)
            
            return self.get_office(office.office_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating office: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_office(self, office_id: int, update_data: OfficeUpdate, request) -> OfficeResponse:
        """Update an existing office."""
        logger.info(f"Updating office: {office_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Get office
            office = self.office_repo.get_by_id(office_id)
            if not office:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Office not found"
                )
            
            # Update office
            update_dict = update_data.dict(exclude_none=True)
            self.office_repo.update(office, update_dict, updated_by=current_user_id)
            
            return self.get_office(office_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating office {office_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_office(self, office_id: int, request) -> dict:
        """Delete an office."""
        logger.warning(f"Deleting office: {office_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Check if office exists
            office = self.office_repo.get_by_id(office_id)
            if not office:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Office not found"
                )
            
            # Delete office
            success = self.office_repo.delete(office_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Office not found"
                )
            
            return {"message": "Office deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting office {office_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_nearby_offices(self, request_data: NearbyOfficeRequest, request) -> List[NearbyOfficeResponse]:
        """Get offices within a radius."""
        logger.info(f"Finding offices near {request_data.latitude}, {request_data.longitude}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            offices_with_distance = self.office_repo.get_nearby_offices(
                latitude=request_data.latitude,
                longitude=request_data.longitude,
                radius_km=request_data.radius_km,
                limit=request_data.limit
            )
            
            # Convert to responses
            responses = []
            for office, distance in offices_with_distance:
                response_data = {
                    'office_id': office.office_id,
                    'office_name': office.office_name,
                    'latitude': office.latitude,
                    'longitude': office.longitude,
                    'updated_by': office.updated_by,
                    'updated_at': office.updated_at,
                    'distance_km': round(distance, 2)
                }
                
                # Add related data if available
                if hasattr(office, 'updater') and office.updater:
                    response_data['updated_by_name'] = office.updater.full_name
                
                responses.append(NearbyOfficeResponse(**response_data))
            
            return responses
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error finding nearby offices: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )