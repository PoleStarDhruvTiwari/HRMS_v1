# app/apis/organization/shifts/services.py
import logging
from typing import List
from datetime import time
from fastapi import HTTPException, status

from app.core.security import security_service
from .repositories import ShiftRepository
from .schemas import ShiftCreate, ShiftUpdate, ShiftResponse, ShiftListResponse

logger = logging.getLogger(__name__)


class ShiftService:
    """Service for shift business logic."""
    
    def __init__(self, shift_repo: ShiftRepository):
        self.shift_repo = shift_repo
    
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
    
    def calculate_duration(self, start_time: time, end_time: time) -> float:
        """Calculate shift duration in hours."""
        from datetime import datetime
        
        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = datetime.combine(datetime.today(), end_time)
        
        # Handle overnight shifts
        if end_dt <= start_dt:
            end_dt = end_dt.replace(day=end_dt.day + 1)
        
        duration = (end_dt - start_dt).total_seconds() / 3600
        return round(duration, 2)
    
    def get_shift(self, shift_id: int, request) -> ShiftResponse:
        """Get shift by ID."""
        logger.debug(f"Getting shift: {shift_id}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            shift = self.shift_repo.get_by_id(shift_id)
            if not shift:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shift not found"
                )
            
            # Calculate duration
            duration = self.calculate_duration(shift.start_time, shift.end_time)
            
            # Convert to response
            response_data = {
                'shift_id': shift.shift_id,
                'shift_name': shift.shift_name,
                'start_time': shift.start_time,
                'end_time': shift.end_time,
                'updated_by': shift.updated_by,
                'updated_at': shift.updated_at,
                'duration_hours': duration
            }
            
            # Add related data if available
            if hasattr(shift, 'updater') and shift.updater:
                response_data['updated_by_name'] = shift.updater.full_name
            
            return ShiftResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting shift {shift_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_shifts(self, request, skip: int = 0, limit: int = 100) -> ShiftListResponse:
        """Get all shifts with pagination."""
        logger.debug(f"Getting shifts (skip: {skip}, limit: {limit})")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            shifts = self.shift_repo.get_all(skip=skip, limit=limit)
            total = self.shift_repo.get_count()
            
            # Convert to responses
            shift_responses = []
            for shift in shifts:
                duration = self.calculate_duration(shift.start_time, shift.end_time)
                
                response_data = {
                    'shift_id': shift.shift_id,
                    'shift_name': shift.shift_name,
                    'start_time': shift.start_time,
                    'end_time': shift.end_time,
                    'updated_by': shift.updated_by,
                    'updated_at': shift.updated_at,
                    'duration_hours': duration
                }
                
                # Add related data if available
                if hasattr(shift, 'updater') and shift.updater:
                    response_data['updated_by_name'] = shift.updater.full_name
                
                shift_responses.append(ShiftResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return ShiftListResponse(
                shifts=shift_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting shifts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def search_shifts(self, search_term: str, request, skip: int = 0, limit: int = 100) -> ShiftListResponse:
        """Search shifts by name."""
        logger.debug(f"Searching shifts: {search_term}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            shifts, total = self.shift_repo.search(search_term, skip=skip, limit=limit)
            
            # Convert to responses
            shift_responses = []
            for shift in shifts:
                duration = self.calculate_duration(shift.start_time, shift.end_time)
                
                response_data = {
                    'shift_id': shift.shift_id,
                    'shift_name': shift.shift_name,
                    'start_time': shift.start_time,
                    'end_time': shift.end_time,
                    'updated_by': shift.updated_by,
                    'updated_at': shift.updated_at,
                    'duration_hours': duration
                }
                
                # Add related data if available
                if hasattr(shift, 'updater') and shift.updater:
                    response_data['updated_by_name'] = shift.updater.full_name
                
                shift_responses.append(ShiftResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return ShiftListResponse(
                shifts=shift_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error searching shifts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_shift(self, shift_data: ShiftCreate, request) -> ShiftResponse:
        """Create a new shift."""
        logger.info(f"Creating new shift: {shift_data.shift_name}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Convert to dict and create
            shift_dict = shift_data.dict()
            shift = self.shift_repo.create(shift_dict, updated_by=current_user_id)
            
            return self.get_shift(shift.shift_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating shift: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_shift(self, shift_id: int, update_data: ShiftUpdate, request) -> ShiftResponse:
        """Update an existing shift."""
        logger.info(f"Updating shift: {shift_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Get shift
            shift = self.shift_repo.get_by_id(shift_id)
            if not shift:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shift not found"
                )
            
            # Update shift
            update_dict = update_data.dict(exclude_none=True)
            self.shift_repo.update(shift, update_dict, updated_by=current_user_id)
            
            return self.get_shift(shift_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating shift {shift_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_shift(self, shift_id: int, request) -> dict:
        """Delete a shift."""
        logger.warning(f"Deleting shift: {shift_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Check if shift exists
            shift = self.shift_repo.get_by_id(shift_id)
            if not shift:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shift not found"
                )
            
            # Delete shift
            success = self.shift_repo.delete(shift_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shift not found"
                )
            
            return {"message": "Shift deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting shift {shift_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )