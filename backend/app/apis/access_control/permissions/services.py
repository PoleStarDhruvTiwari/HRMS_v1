# app/apis/access_control/permissions/services.py
"""
Service for READ-ONLY permission operations.
"""

import logging
from typing import List
from fastapi import HTTPException, status

from app.core.security import security_service
from .repositories import PermissionRepository
from .schemas import PermissionResponse, PermissionListResponse, PermissionGroupResponse

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for permission READ-ONLY business logic."""
    
    def __init__(self, permission_repo: PermissionRepository):
        self.permission_repo = permission_repo
    
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
    
    def get_permission(self, permission_id: int, request) -> PermissionResponse:
        """Get permission by ID."""
        logger.debug(f"Getting permission: {permission_id}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
            permission = self.permission_repo.get_by_id(permission_id)
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Permission not found"
                )
            
            # Get role count
            role_count = self.permission_repo.get_role_count(permission_id)
            
            # Convert to response
            response_data = {
                'permission_id': permission.permission_id,
                'permission_key': permission.permission_key,
                'description': permission.description,
                'status': permission.status,
                'updated_by': permission.updated_by,
                'updated_at': permission.updated_at,
                'role_count': role_count
            }
            
            # Add related data if available
            if hasattr(permission, 'updater') and permission.updater:
                response_data['updated_by_name'] = permission.updater.full_name
            
            return PermissionResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting permission {permission_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_permission_by_key(self, permission_key: str, request) -> PermissionResponse:
        """Get permission by key."""
        logger.debug(f"Getting permission by key: {permission_key}")
        
        try:
            self.get_current_user_id(request)
            
            permission = self.permission_repo.get_by_key(permission_key)
            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Permission not found"
                )
            
            # Get role count
            role_count = self.permission_repo.get_role_count(permission.permission_id)
            
            # Convert to response
            response_data = {
                'permission_id': permission.permission_id,
                'permission_key': permission.permission_key,
                'description': permission.description,
                'status': permission.status,
                'updated_by': permission.updated_by,
                'updated_at': permission.updated_at,
                'role_count': role_count
            }
            
            # Add related data if available
            if hasattr(permission, 'updater') and permission.updater:
                response_data['updated_by_name'] = permission.updater.full_name
            
            return PermissionResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting permission by key {permission_key}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_permissions(self, request, active_only: bool = True, 
                       skip: int = 0, limit: int = 100) -> PermissionListResponse:
        """Get all permissions with pagination."""
        logger.debug(f"Getting permissions (active_only: {active_only}, skip: {skip}, limit: {limit})")
        
        try:
            self.get_current_user_id(request)
            
            permissions_with_counts = self.permission_repo.get_permissions_with_role_counts(
                skip=skip, limit=limit, active_only=active_only
            )
            total = self.permission_repo.get_count(active_only=active_only)
            
            # Convert to responses
            permission_responses = []
            for permission, role_count in permissions_with_counts:
                response_data = {
                    'permission_id': permission.permission_id,
                    'permission_key': permission.permission_key,
                    'description': permission.description,
                    'status': permission.status,
                    'updated_by': permission.updated_by,
                    'updated_at': permission.updated_at,
                    'role_count': role_count
                }
                
                # Add related data if available
                if hasattr(permission, 'updater') and permission.updater:
                    response_data['updated_by_name'] = permission.updater.full_name
                
                permission_responses.append(PermissionResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return PermissionListResponse(
                permissions=permission_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_permissions_grouped_by_module(self, request, active_only: bool = True) -> List[PermissionGroupResponse]:
        """Get permissions grouped by their module prefix."""
        logger.debug(f"Getting permissions grouped by module (active_only: {active_only})")
        
        try:
            self.get_current_user_id(request)
            
            # Get all permissions
            permissions = self.permission_repo.get_all(active_only=active_only)
            
            # Group by module
            module_groups = {}
            for permission in permissions:
                # Extract module from permission key (e.g., "attendance.mark" -> "attendance")
                parts = permission.permission_key.split('.')
                module = parts[0] if parts else 'other'
                
                if module not in module_groups:
                    module_groups[module] = []
                
                # Get role count
                role_count = self.permission_repo.get_role_count(permission.permission_id)
                
                # Create response data
                response_data = {
                    'permission_id': permission.permission_id,
                    'permission_key': permission.permission_key,
                    'description': permission.description,
                    'status': permission.status,
                    'updated_by': permission.updated_by,
                    'updated_at': permission.updated_at,
                    'role_count': role_count
                }
                
                if hasattr(permission, 'updater') and permission.updater:
                    response_data['updated_by_name'] = permission.updater.full_name
                
                module_groups[module].append(PermissionResponse(**response_data))
            
            # Convert to response format
            result = []
            for module, perms in sorted(module_groups.items()):
                result.append(PermissionGroupResponse(
                    module=module,
                    permissions=sorted(perms, key=lambda p: p.permission_key)
                ))
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting permissions grouped by module: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )