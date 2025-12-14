# app/apis/users/services.py
import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, UploadFile, File
from datetime import datetime

from app.core.security import security_service
from .repositories import UserRepository
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, 
    UserProfileResponse, UserFilter, UserBulkUpdate
)

logger = logging.getLogger(__name__)


class UserService:
    """Service for user business logic."""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
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
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    def get_user(self, user_id: int, request) -> UserResponse:
        """Get user by ID."""
        logger.debug(f"Getting user: {user_id}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserResponse.from_orm(user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_users(self, request, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users with pagination."""
        logger.debug(f"Getting users (skip: {skip}, limit: {limit})")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            users = self.user_repo.get_all(skip=skip, limit=limit)
            return [UserResponse.from_orm(user) for user in users]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting users: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def search_users(self, filters: UserFilter, request, skip: int = 0, limit: int = 100,
                    sort_by: str = "user_id", sort_order: str = "asc") -> UserListResponse:
        """Search users with filters."""
        logger.debug(f"Searching users with filters")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            users, total = self.user_repo.search_users(
                filters=filters,
                skip=skip,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return UserListResponse(
                users=[UserResponse.from_orm(user) for user in users],
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error searching users: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_user(self, user_data: UserCreate, request) -> UserResponse:
        """Create a new user."""
        logger.info(f"Creating new user: {user_data.email}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for user creation
            self.verify_admin_access(current_user_id)
            
            # Check if email already exists
            existing_user = self.user_repo.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Convert to dict and create user
            user_dict = user_data.dict(exclude_none=True)
            user = self.user_repo.create(user_dict, created_by=current_user_id)
            
            return UserResponse.from_orm(user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_user(self, user_id: int, update_data: UserUpdate, request) -> UserResponse:
        """Update an existing user."""
        logger.info(f"Updating user: {user_id}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Get user to update
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if trying to update email that already exists
            if update_data.email and update_data.email != user.email:
                existing_user = self.user_repo.get_by_email(update_data.email)
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
            
            # Update user
            update_dict = update_data.dict(exclude_none=True)
            updated_user = self.user_repo.update(user, update_dict, updated_by=current_user_id)
            
            return UserResponse.from_orm(updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def bulk_update_users(self, bulk_data: UserBulkUpdate, request) -> Dict[str, Any]:
        """Update multiple users at once."""
        logger.info(f"Bulk updating {len(bulk_data.user_ids)} users")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for bulk operations
            self.verify_admin_access(current_user_id)
            
            # Prepare update data
            update_data = bulk_data.dict(exclude_none=True, exclude={'user_ids'})
            
            # Perform bulk update
            updated_count = self.user_repo.bulk_update(
                user_ids=bulk_data.user_ids,
                update_data=update_data,
                updated_by=current_user_id
            )
            
            return {
                "message": f"Successfully updated {updated_count} users",
                "updated_count": updated_count,
                "total_requested": len(bulk_data.user_ids)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error in bulk update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_user(self, user_id: int, request) -> Dict[str, str]:
        """Delete a user."""
        logger.warning(f"Deleting user: {user_id}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for deletion
            self.verify_admin_access(current_user_id)
            
            # Prevent self-deletion
            if user_id == current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete your own account"
                )
            
            # Delete user
            success = self.user_repo.delete(user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return {"message": "User deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_user_profile(self, user_id: int, request) -> UserProfileResponse:
        """Get user profile with related data."""
        logger.debug(f"Getting profile for user: {user_id}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            profile_data = self.user_repo.get_user_profile(user_id)
            if not profile_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user = profile_data["user"]
            profile_response = UserProfileResponse(
                **UserResponse.from_orm(user).dict(),
                reporting_level1_name=profile_data["reporting_level1_name"],
                reporting_level2_name=profile_data["reporting_level2_name"],
                updater_name=profile_data["updater_name"]
            )
            
            return profile_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting user profile {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_user_resume(self, user_id: int, resume_file: UploadFile, request) -> Dict[str, Any]:
        """Upload/update user resume."""
        logger.info(f"Updating resume for user: {user_id}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Get user
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check permissions (user can update own resume, admin can update any)
            if user_id != current_user_id:
                self.verify_admin_access(current_user_id)
            
            # Read file content
            file_content = await resume_file.read()
            
            # Update user resume
            update_data = {
                "resume": file_content.decode('utf-8')  # Convert to string for Text field
            }
            
            updated_user = self.user_repo.update(user, update_data, updated_by=current_user_id)
            
            return {
                "message": "Resume updated successfully",
                "file_name": resume_file.filename,
                "file_type": resume_file.content_type,
                "file_size": len(file_content),
                "user_id": user_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating resume for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_user_counts(self, request) -> Dict[str, Any]:
        """Get user statistics."""
        logger.debug("Getting user counts")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for statistics
            self.verify_admin_access(current_user_id)
            
            counts = self.user_repo.get_user_count()
            return counts
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting user counts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )