# app/apis/organization/designations/services.py
import logging
from typing import List
from fastapi import HTTPException, status

from app.core.security import security_service
from .repositories import DesignationRepository
from .schemas import DesignationCreate, DesignationUpdate, DesignationResponse, DesignationListResponse

logger = logging.getLogger(__name__)


class DesignationService:
    """Service for designation business logic."""
    
    def __init__(self, designation_repo: DesignationRepository):
        self.designation_repo = designation_repo
    
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
    
    def get_designation(self, designation_id: int, request) -> DesignationResponse:
        """Get designation by ID."""
        logger.debug(f"Getting designation: {designation_id}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            designation = self.designation_repo.get_by_id(designation_id)
            if not designation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Designation not found"
                )
            
            # Get user count
            user_count = self.designation_repo.get_user_count(designation_id)
            
            # Convert to response
            response_data = {
                'designation_id': designation.designation_id,
                'designation_code': designation.designation_code,
                'designation_name': designation.designation_name,
                'updated_by': designation.updated_by,
                'updated_at': designation.updated_at,
                'user_count': user_count
            }
            
            # Add related data if available
            if hasattr(designation, 'updater') and designation.updater:
                response_data['updated_by_name'] = designation.updater.full_name
            
            return DesignationResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting designation {designation_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_designations(self, request, skip: int = 0, limit: int = 100) -> DesignationListResponse:
        """Get all designations with pagination."""
        logger.debug(f"Getting designations (skip: {skip}, limit: {limit})")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            designations_with_counts = self.designation_repo.get_designations_with_user_counts(skip=skip, limit=limit)
            total = self.designation_repo.get_count()
            
            # Convert to responses
            designation_responses = []
            for designation, user_count in designations_with_counts:
                response_data = {
                    'designation_id': designation.designation_id,
                    'designation_code': designation.designation_code,
                    'designation_name': designation.designation_name,
                    'updated_by': designation.updated_by,
                    'updated_at': designation.updated_at,
                    'user_count': user_count
                }
                
                # Add related data if available
                if hasattr(designation, 'updater') and designation.updater:
                    response_data['updated_by_name'] = designation.updater.full_name
                
                designation_responses.append(DesignationResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return DesignationListResponse(
                designations=designation_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting designations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def search_designations(self, search_term: str, request, skip: int = 0, limit: int = 100) -> DesignationListResponse:
        """Search designations by code or name."""
        logger.debug(f"Searching designations: {search_term}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            designations, total = self.designation_repo.search(search_term, skip=skip, limit=limit)
            
            # Convert to responses
            designation_responses = []
            for designation in designations:
                user_count = self.designation_repo.get_user_count(designation.designation_id)
                
                response_data = {
                    'designation_id': designation.designation_id,
                    'designation_code': designation.designation_code,
                    'designation_name': designation.designation_name,
                    'updated_by': designation.updated_by,
                    'updated_at': designation.updated_at,
                    'user_count': user_count
                }
                
                # Add related data if available
                if hasattr(designation, 'updater') and designation.updater:
                    response_data['updated_by_name'] = designation.updater.full_name
                
                designation_responses.append(DesignationResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return DesignationListResponse(
                designations=designation_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error searching designations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_designation(self, designation_data: DesignationCreate, request) -> DesignationResponse:
        """Create a new designation."""
        logger.info(f"Creating new designation: {designation_data.designation_code}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Convert to dict and create
            designation_dict = designation_data.dict(exclude_none=True)
            designation = self.designation_repo.create(designation_dict, updated_by=current_user_id)
            
            return self.get_designation(designation.designation_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating designation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_designation(self, designation_id: int, update_data: DesignationUpdate, request) -> DesignationResponse:
        """Update an existing designation."""
        logger.info(f"Updating designation: {designation_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Get designation
            designation = self.designation_repo.get_by_id(designation_id)
            if not designation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Designation not found"
                )
            
            # Update designation
            update_dict = update_data.dict(exclude_none=True)
            self.designation_repo.update(designation, update_dict, updated_by=current_user_id)
            
            return self.get_designation(designation_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating designation {designation_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_designation(self, designation_id: int, request) -> dict:
        """Delete a designation."""
        logger.warning(f"Deleting designation: {designation_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Check if designation exists
            designation = self.designation_repo.get_by_id(designation_id)
            if not designation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Designation not found"
                )
            
            # Delete designation
            try:
                success = self.designation_repo.delete(designation_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Designation not found"
                    )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            
            return {"message": "Designation deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting designation {designation_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )