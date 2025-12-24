# app/apis/access_control/role_permissions/services.py
"""
Service for Role Permission business logic.
"""

import logging
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import security_service
from app.core.permission_checker import PermissionChecker
from .repositories import RolePermissionRepository
from .schemas import RolePermissionAssign, RolePermissionBulkAssign, RolePermissionRemove

logger = logging.getLogger(__name__)


class RolePermissionService:
    """Service for role permission operations."""
    
    def __init__(self, role_perm_repo: RolePermissionRepository, db: Session):
        self.role_perm_repo = role_perm_repo
        self.db = db
    
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
        from app.apis.auth.models import ExistingUser
        
        user = self.db.query(ExistingUser).filter(
            ExistingUser.user_id == user_id,
            ExistingUser.is_active == True
        ).first()
        
        if not user or not user.is_admin:
            logger.warning(f"User {user_id} attempted admin action without privileges")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    def verify_role_exists(self, role_id: int) -> bool:
        """Verify role exists."""
        from app.apis.access_control.roles.models import Role
        
        role = self.db.query(Role).filter(Role.role_id == role_id).first()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found"
            )
        return True
    
    def verify_permission_exists(self, permission_id: int) -> bool:
        """Verify permission exists and is active."""
        from app.apis.access_control.permissions.models import Permission
        
        permission = self.db.query(Permission).filter(
            Permission.permission_id == permission_id,
            Permission.status == 'active'
        ).first()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission {permission_id} not found or inactive"
            )
        return True
    
    def get_role_permissions(self, role_id: int, request) -> List[dict]:
        """Get all permissions for a role."""
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Verify role exists
            self.verify_role_exists(role_id)
            
            # Get role permissions
            role_perms = self.role_perm_repo.get_role_permissions(role_id)
            
            # Convert to response
            permissions = []
            for rp in role_perms:
                permissions.append({
                    "role_permission_id": rp.role_permission_id,
                    "role_id": rp.role_id,
                    "role_name": rp.role.role_name if rp.role else None,
                    "role_code": rp.role.role_code if rp.role else None,
                    "permission_id": rp.permission_id,
                    "permission_key": rp.permission.permission_key if rp.permission else None,
                    "permission_name": rp.permission.description if rp.permission else None,
                    "updated_by": rp.updated_by,
                    "updated_by_name": rp.updater.full_name if rp.updater else None,
                    "updated_at": rp.updated_at
                })
            
            return permissions
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting permissions for role {role_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_roles_with_permission(self, permission_id: int, request) -> List[dict]:
        """Get all roles that have a specific permission."""
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Verify permission exists
            self.verify_permission_exists(permission_id)
            
            # Get roles with permission
            role_perms = self.role_perm_repo.get_roles_with_permission(permission_id)
            
            # Convert to response
            roles = []
            for rp in role_perms:
                roles.append({
                    "role_id": rp.role_id,
                    "role_name": rp.role.role_name if rp.role else None,
                    "role_code": rp.role.role_code if rp.role else None,
                    "role_permission_id": rp.role_permission_id,
                    "updated_by": rp.updated_by,
                    "updated_by_name": rp.updater.full_name if rp.updater else None,
                    "updated_at": rp.updated_at
                })
            
            return roles
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting roles with permission {permission_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def assign_permission(self, assign_data: RolePermissionAssign, request) -> dict:
        """Assign permission to role."""
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Verify role and permission exist
            self.verify_role_exists(assign_data.role_id)
            self.verify_permission_exists(assign_data.permission_id)
            
            # Assign permission
            role_perm = self.role_perm_repo.assign_permission(
                role_id=assign_data.role_id,
                permission_id=assign_data.permission_id,
                updated_by=current_user_id
            )
            
            return {
                "message": "Permission assigned to role successfully",
                "role_permission_id": role_perm.role_permission_id,
                "role_id": role_perm.role_id,
                "permission_id": role_perm.permission_id,
                "updated_by": role_perm.updated_by,
                "updated_at": role_perm.updated_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error assigning permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def remove_permission(self, remove_data: RolePermissionRemove, request) -> dict:
        """Remove permission from role."""
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            if remove_data.role_permission_id:
                # Remove by role_permission_id
                success = self.role_perm_repo.remove_permission(remove_data.role_permission_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Role permission not found"
                    )
            else:
                # Remove by role_id + permission_id
                if not remove_data.role_id or not remove_data.permission_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="role_id and permission_id are required when not using role_permission_id"
                    )
                
                success = self.role_perm_repo.remove_by_role_and_permission(
                    remove_data.role_id, remove_data.permission_id
                )
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Role permission not found"
                    )
            
            return {"message": "Permission removed from role successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error removing permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def bulk_assign_permissions(self, bulk_data: RolePermissionBulkAssign, request) -> dict:
        """Assign multiple permissions to multiple roles in bulk."""
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            logger.info(f"Admin {current_user_id} bulk assigning {len(bulk_data.permission_ids)} permissions to {len(bulk_data.role_ids)} roles")
            
            # Verify all roles exist
            from app.apis.access_control.roles.models import Role
            roles_count = self.db.query(func.count(Role.role_id)).filter(
                Role.role_id.in_(bulk_data.role_ids)
            ).scalar()
            
            if roles_count != len(bulk_data.role_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some roles do not exist"
                )
            
            # Verify all permissions exist and are active
            from app.apis.access_control.permissions.models import Permission
            perms_count = self.db.query(func.count(Permission.permission_id)).filter(
                Permission.permission_id.in_(bulk_data.permission_ids),
                Permission.status == 'active'
            ).scalar()
            
            if perms_count != len(bulk_data.permission_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some permissions do not exist or are inactive"
                )
            
            # Bulk assign
            assigned = self.role_perm_repo.bulk_assign_permissions(
                bulk_data.role_ids,
                bulk_data.permission_ids,
                current_user_id
            )
            
            logger.info(f"Bulk assign completed: {len(assigned)} successful assignments")
            
            return {
                "message": f"Permissions assigned successfully",
                "total_attempted": len(bulk_data.role_ids) * len(bulk_data.permission_ids),
                "successfully_assigned": len(assigned),
                "duplicates_skipped": (len(bulk_data.role_ids) * len(bulk_data.permission_ids)) - len(assigned)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error in bulk assign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )