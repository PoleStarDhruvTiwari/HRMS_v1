import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
# Add this import at the top with other imports
from app.apis.auth.models import ExistingUser

from app.core.base_service import BaseService
from .repositories import EmployeeHierarchyRepository
from .schemas import (
    NewEmployeeHierarchyCreate,
    EmployeeHierarchyResponse,
    EmployeeHierarchyListResponse,
    HierarchyCreationResponse
)

logger = logging.getLogger(__name__)


class EmployeeHierarchyService(BaseService):
    """Service for employee hierarchy business logic."""
    
    def __init__(self, hierarchy_repo: EmployeeHierarchyRepository, db: Session):
        super().__init__(db)
        self.hierarchy_repo = hierarchy_repo
        self.db = db
    
    def get_hierarchy_entries_for_user(self, user_id: int, request) -> List[EmployeeHierarchyResponse]:
        """Get ALL hierarchy entries for a specific user."""
        logger.debug(f"Getting all hierarchy entries for user: {user_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "hierarchy.view")
            
            entries = self.hierarchy_repo.get_all_by_user_id(user_id)
            if not entries:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No hierarchy entries found for user: {user_id}"
                )
            
            responses = []
            for entry in entries:
                response_data = {
                    "id": entry.id,
                    "user_id": entry.user_id,
                    "reporting_to_id": entry.reporting_to_id,
                    "depth": entry.depth,
                    "updated_by": entry.updated_by,
                    "updated_at": entry.updated_at,
                    "employee_name": self._get_user_name(entry.user_id),
                    "reporting_to_name": self._get_user_name(entry.reporting_to_id) if entry.reporting_to_id else None,
                    "updated_by_name": self._get_user_name(entry.updated_by) if entry.updated_by else None
                }
                responses.append(EmployeeHierarchyResponse(**response_data))
            
            return responses
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting hierarchy entries for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_all_hierarchies(self, request, skip: int = 0, limit: int = 100) -> EmployeeHierarchyListResponse:
        """Get all hierarchy entries with pagination."""
        logger.debug(f"Getting all hierarchy entries (skip: {skip}, limit: {limit})")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "hierarchy.view")
            
            entries = self.hierarchy_repo.get_all(skip=skip, limit=limit)
            total = self.hierarchy_repo.get_count()
            
            responses = []
            for entry in entries:
                response_data = {
                    "id": entry.id,
                    "user_id": entry.user_id,
                    "reporting_to_id": entry.reporting_to_id,
                    "depth": entry.depth,
                    "updated_by": entry.updated_by,
                    "updated_at": entry.updated_at,
                    "employee_name": self._get_user_name(entry.user_id),
                    "reporting_to_name": self._get_user_name(entry.reporting_to_id) if entry.reporting_to_id else None,
                    "updated_by_name": self._get_user_name(entry.updated_by) if entry.updated_by else None
                }
                responses.append(EmployeeHierarchyResponse(**response_data))
            
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return EmployeeHierarchyListResponse(
                entries=responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting all hierarchy entries: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_complete_hierarchy_for_new_employee(self, create_data: NewEmployeeHierarchyCreate, request) -> HierarchyCreationResponse:
        """
        Create complete reporting chain for a new employee.
        
        This creates:
        1. Direct reporting entry (depth 1)
        2. Indirect reporting entries for all managers in the chain
        """
        logger.info(f"Creating complete hierarchy for new employee: {create_data.user_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "hierarchy.create")
            
            # Check if user already has any hierarchy entries
            existing_entries = self.hierarchy_repo.get_all_by_user_id(create_data.user_id)
            if existing_entries:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {create_data.user_id} already has hierarchy entries"
                )
            
            # Create complete reporting chain
            entries_created = self.hierarchy_repo.create_complete_reporting_chain(
                user_id=create_data.user_id,
                first_reporting_to_id=create_data.first_reportee_id,
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
                    "user_id": entry.user_id,
                    "reporting_to_id": entry.reporting_to_id,
                    "depth": entry.depth,
                    "updated_by": entry.updated_by,
                    "updated_at": entry.updated_at,
                    "employee_name": self._get_user_name(entry.user_id),
                    "reporting_to_name": self._get_user_name(entry.reporting_to_id) if entry.reporting_to_id else None,
                    "updated_by_name": self._get_user_name(entry.updated_by) if entry.updated_by else None
                }
                entry_responses.append(EmployeeHierarchyResponse(**response_data))
            
            return HierarchyCreationResponse(
                message=f"Created {len(entries_created)} hierarchy entries successfully",
                new_employee_entry=entry_responses[0] if entry_responses else None
            )
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating complete hierarchy for new employee: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_hierarchy_entries(self, user_id: int, request) -> dict:
        """Delete ALL hierarchy entries for a user."""
        logger.warning(f"Deleting all hierarchy entries for user: {user_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_permission(current_user_id, "hierarchy.delete")
            
            success = self.hierarchy_repo.delete_by_user_id(user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No hierarchy entries found for user: {user_id}"
                )
            
            return {"message": f"All hierarchy entries deleted successfully for user: {user_id}"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting hierarchy entries: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _get_user_name(self, user_id: int) -> Optional[str]:
        """Get user name by ID from ExistingUser model."""
        try:
            user = self.db.query(ExistingUser).filter(ExistingUser.user_id == user_id).first()
            if user and user.full_name:
                return user.full_name
            return f"User {user_id}"
        except Exception as e:
            logger.error(f"Error getting user name for {user_id}: {str(e)}")
            return f"User {user_id}"