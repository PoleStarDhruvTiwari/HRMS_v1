# app/apis/roles/services.py
import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from app.core.security import security_service
from .repositories import RoleRepository
from .schemas import (
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
    RoleFilter, RoleBulkUpdate
)

logger = logging.getLogger(__name__)


class RoleService:
    """Service for role business logic."""
    
    def __init__(self, role_repo: RoleRepository):
        self.role_repo = role_repo
    
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
        # Import user repository to check admin status
        from app.database.session import SessionLocal
        from app.apis.users.repositories import UserRepository
        
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            user = user_repo.get_by_id(user_id)
            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
        finally:
            db.close()
    
    def get_role(self, role_id: int, request) -> RoleResponse:
        """Get role by ID."""
        logger.debug(f"Getting role: {role_id}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            role = self.role_repo.get_by_id(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            # Convert to response
            response_data = {
                'role_id': role.role_id,
                'role_code': role.role_code,
                'role_name': role.role_name,
                'description': role.description,
                'updated_by_id': role.updated_by_id,
                'updated_at': role.updated_at,
            }
            
            # Add related data if available
            if hasattr(role, 'updated_by') and role.updated_by:
                response_data['updated_by_name'] = role.updated_by.full_name
            
            return RoleResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting role {role_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_roles(self, request, skip: int = 0, limit: int = 100) -> List[RoleResponse]:
        """Get all roles with pagination."""
        logger.debug(f"Getting roles (skip: {skip}, limit: {limit})")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            roles = self.role_repo.get_all(skip=skip, limit=limit)
            
            # Convert to responses
            role_responses = []
            for role in roles:
                response_data = {
                    'role_id': role.role_id,
                    'role_code': role.role_code,
                    'role_name': role.role_name,
                    'description': role.description,
                    'updated_by_id': role.updated_by_id,
                    'updated_at': role.updated_at,
                }
                
                # Add related data if available
                if hasattr(role, 'updated_by') and role.updated_by:
                    response_data['updated_by_name'] = role.updated_by.full_name
                
                role_responses.append(RoleResponse(**response_data))
            
            return role_responses
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def search_roles(self, filters: RoleFilter, request, skip: int = 0, limit: int = 100,
                    sort_by: str = "role_code", sort_order: str = "asc") -> RoleListResponse:
        """Search roles with filters."""
        logger.debug(f"Searching roles with filters")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            roles, total = self.role_repo.search_roles(
                filters=filters,
                skip=skip,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # Convert to responses
            role_responses = []
            for role in roles:
                response_data = {
                    'role_id': role.role_id,
                    'role_code': role.role_code,
                    'role_name': role.role_name,
                    'description': role.description,
                    'updated_by_id': role.updated_by_id,
                    'updated_at': role.updated_at,
                }
                
                # Add related data if available
                if hasattr(role, 'updated_by') and role.updated_by:
                    response_data['updated_by_name'] = role.updated_by.full_name
                
                role_responses.append(RoleResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return RoleListResponse(
                roles=role_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error searching roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_role(self, role_data: RoleCreate, request) -> RoleResponse:
        """Create a new role."""
        logger.info(f"Creating new role: {role_data.role_code}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for role creation
            self.verify_admin_access(current_user_id)
            
            # Convert to dict and create role
            role_dict = role_data.dict(exclude_none=True)
            role = self.role_repo.create(role_dict, updated_by_id=current_user_id)
            
            return self.get_role(role.role_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_role(self, role_id: int, update_data: RoleUpdate, request) -> RoleResponse:
        """Update an existing role."""
        logger.info(f"Updating role: {role_id}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for role updates
            self.verify_admin_access(current_user_id)
            
            # Get role
            role = self.role_repo.get_by_id(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            # Update role
            update_dict = update_data.dict(exclude_none=True)
            self.role_repo.update(role, update_dict, updated_by_id=current_user_id)
            
            return self.get_role(role_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating role {role_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def bulk_update_roles(self, bulk_data: RoleBulkUpdate, request) -> Dict[str, Any]:
        """Update multiple roles at once."""
        logger.info(f"Bulk updating {len(bulk_data.role_ids)} roles")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for bulk operations
            self.verify_admin_access(current_user_id)
            
            # Prepare update data
            update_data = bulk_data.dict(exclude_none=True, exclude={'role_ids'})
            
            # Perform bulk update
            updated_count = self.role_repo.bulk_update(
                role_ids=bulk_data.role_ids,
                update_data=update_data,
                updated_by_id=current_user_id
            )
            
            return {
                "message": f"Successfully updated {updated_count} roles",
                "updated_count": updated_count,
                "total_requested": len(bulk_data.role_ids)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error in bulk update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_role(self, role_id: int, request) -> Dict[str, str]:
        """Delete a role."""
        logger.warning(f"Deleting role: {role_id}")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for deletion
            self.verify_admin_access(current_user_id)
            
            # Get role first to check if it exists
            role = self.role_repo.get_by_id(role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role not found"
                )
            
            # Delete role
            try:
                success = self.role_repo.delete(role_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Role not found"
                    )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            
            return {"message": "Role deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting role {role_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_role_counts(self, request) -> Dict[str, Any]:
        """Get role statistics."""
        logger.debug("Getting role counts")
        
        try:
            # Get current user for audit
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for statistics
            self.verify_admin_access(current_user_id)
            
            counts = self.role_repo.get_role_counts()
            return counts
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting role counts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_default_roles(self) -> List[RoleResponse]:
        """Get default system roles."""
        logger.debug("Getting default roles")
        
        try:
            # Define default roles (you can customize these)
            default_role_codes = ['ADMIN', 'MANAGER', 'EMPLOYEE', 'VIEWER']
            
            roles = []
            for role_code in default_role_codes:
                role = self.role_repo.get_by_code(role_code)
                if role:
                    response_data = {
                        'role_id': role.role_id,
                        'role_code': role.role_code,
                        'role_name': role.role_name,
                        'description': role.description,
                        'updated_by_id': role.updated_by_id,
                        'updated_at': role.updated_at,
                    }
                    
                    if hasattr(role, 'updated_by') and role.updated_by:
                        response_data['updated_by_name'] = role.updated_by.full_name
                    
                    roles.append(RoleResponse(**response_data))
            
            return roles
            
        except Exception as e:
            logger.exception(f"Error getting default roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )