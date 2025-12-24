# app/apis/access_control/user_permissions/services.py
"""
Service for User Permission business logic.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import security_service
from .repositories import UserPermissionRepository
from .schemas import (
    UserPermissionGrant, UserPermissionRevoke, UserPermissionBulkGrant,
    UserPermissionResponse, EffectivePermissionsResponse
)

logger = logging.getLogger(__name__)


class UserPermissionService:
    """Service for user permission operations."""
    
    def __init__(self, user_perm_repo: UserPermissionRepository, db: Session):
        self.user_perm_repo = user_perm_repo
        self.db = db
    
    def get_current_user_id(self, request) -> int:
        """Extract and verify current user ID from request token."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.error("No authorization header provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        try:
            access_token = security_service.extract_token_from_header(auth_header)
            payload = security_service.verify_local_token(access_token)
            user_id = payload.get("user_id")
            
            if not user_id:
                logger.error("No user_id found in token payload")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Verify user exists and is active
            from app.apis.auth.models import ExistingUser
            user = self.db.query(ExistingUser).filter(
                ExistingUser.user_id == user_id,
                ExistingUser.is_active == True
            ).first()
            
            if not user:
                logger.error(f"User {user_id} not found or inactive")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            return user_id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    def verify_admin_access(self, user_id: int):
        """Verify user has admin privileges."""
        from app.apis.auth.models import ExistingUser
        
        user = self.db.query(ExistingUser).filter(
            ExistingUser.user_id == user_id,
            ExistingUser.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_admin:
            logger.warning(f"User {user_id} attempted admin action without privileges")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    def verify_user_exists(self, user_id: int) -> bool:
        """Verify user exists and is active."""
        from app.apis.auth.models import ExistingUser
        
        user = self.db.query(ExistingUser).filter(
            ExistingUser.user_id == user_id,
            ExistingUser.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found or inactive"
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
    
    def get_user_permissions(self, user_id: int, request) -> List[UserPermissionResponse]:
        """Get all permissions for a specific user."""
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ Verify token
            
            # Users can view their own permissions, admins can view anyone's
            if current_user_id != user_id:
                self.verify_admin_access(current_user_id)  # ✅ Admin check
            
            # Verify user exists
            self.verify_user_exists(user_id)
            
            # Get user permissions
            user_perms = self.user_perm_repo.get_user_permissions(user_id, active_only=True)
            
            # Convert to response
            responses = []
            for up in user_perms:
                response = UserPermissionResponse(
                    user_permission_id=up.user_permission_id,
                    user_id=up.user_id,
                    permission_id=up.permission_id,
                    permission_key=up.permission.permission_key if up.permission else None,
                    permission_name=up.permission.description if up.permission else None,
                    granted_by=up.granted_by,
                    granted_by_name=up.granter.full_name if up.granter else None,
                    granted_at=up.granted_at,
                    revoked_at=up.revoked_at,
                    status="active" if not up.revoked_at else "revoked"
                )
                responses.append(response)
            
            logger.info(f"Retrieved {len(responses)} permissions for user {user_id} (requested by user {current_user_id})")
            return responses
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting permissions for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_users_with_permission(self, permission_id: int, request) -> List[dict]:
        """Get all users who have a specific permission."""
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ Verify token
            self.verify_admin_access(current_user_id)  # ✅ Admin only
            
            # Verify permission exists
            self.verify_permission_exists(permission_id)
            
            # Get users with permission
            user_perms = self.user_perm_repo.get_users_with_permission(permission_id, active_only=True)
            
            # Convert to response
            users = []
            for up in user_perms:
                if up.user:
                    users.append({
                        "user_id": up.user_id,
                        "full_name": up.user.full_name,
                        "email": up.user.email,
                        "granted_by": up.granted_by,
                        "granted_by_name": up.granter.full_name if up.granter else None,
                        "granted_at": up.granted_at,
                        "user_permission_id": up.user_permission_id
                    })
            
            logger.info(f"Retrieved {len(users)} users with permission {permission_id} (requested by admin {current_user_id})")
            return users
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting users with permission {permission_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def grant_permission(self, grant_data: UserPermissionGrant, request) -> UserPermissionResponse:
        """Grant permission directly to a user."""
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ Verify token
            self.verify_admin_access(current_user_id)  # ✅ Admin only
            
            # Verify user and permission exist
            self.verify_user_exists(grant_data.user_id)
            self.verify_permission_exists(grant_data.permission_id)
            
            # Check if current user is trying to grant to themselves (allowed for admins)
            if current_user_id == grant_data.user_id:
                logger.warning(f"Admin {current_user_id} is granting permission to themselves")
            
            # Grant permission
            user_perm = self.user_perm_repo.grant_permission(
                user_id=grant_data.user_id,
                permission_id=grant_data.permission_id,
                granted_by=current_user_id
            )
            
            # Get permission details for response
            from app.apis.access_control.permissions.models import Permission
            from app.apis.auth.models import ExistingUser
            
            permission = self.db.query(Permission).filter(
                Permission.permission_id == grant_data.permission_id
            ).first()
            
            granter = self.db.query(ExistingUser).filter(
                ExistingUser.user_id == current_user_id
            ).first()
            
            logger.info(f"Admin {current_user_id} granted permission {grant_data.permission_id} to user {grant_data.user_id}")
            
            return UserPermissionResponse(
                user_permission_id=user_perm.user_permission_id,
                user_id=user_perm.user_id,
                permission_id=user_perm.permission_id,
                permission_key=permission.permission_key if permission else None,
                permission_name=permission.description if permission else None,
                granted_by=user_perm.granted_by,
                granted_by_name=granter.full_name if granter else None,
                granted_at=user_perm.granted_at,
                revoked_at=user_perm.revoked_at,
                status="active" if not user_perm.revoked_at else "revoked"
            )
            
        except ValueError as e:
            logger.warning(f"Grant permission validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error granting permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def revoke_permission(self, revoke_data: UserPermissionRevoke, request) -> dict:
        """Revoke a directly granted permission."""
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ Verify token
            self.verify_admin_access(current_user_id)  # ✅ Admin only
            
            if revoke_data.user_permission_id:
                # Get permission details for logging
                user_perm = self.user_perm_repo.get_by_id(revoke_data.user_permission_id)
                if user_perm:
                    logger.info(f"Admin {current_user_id} revoking user_permission {revoke_data.user_permission_id} (user {user_perm.user_id}, permission {user_perm.permission_id})")
                
                # Revoke by user_permission_id
                success = self.user_perm_repo.revoke_permission(revoke_data.user_permission_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User permission not found or already revoked"
                    )
            else:
                # Revoke by user_id + permission_id
                if not revoke_data.user_id or not revoke_data.permission_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="user_id and permission_id are required when not using user_permission_id"
                    )
                
                logger.info(f"Admin {current_user_id} revoking permission {revoke_data.permission_id} from user {revoke_data.user_id}")
                
                success = self.user_perm_repo.revoke_by_user_and_permission(
                    revoke_data.user_id, revoke_data.permission_id
                )
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User permission not found or already revoked"
                    )
            
            return {"message": "Permission revoked successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error revoking permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_user_permission(self, user_permission_id: int, request) -> dict:
        """Hard delete a user permission record (admin only, for cleanup)."""
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ Verify token
            self.verify_admin_access(current_user_id)  # ✅ Admin only
            
            # Get details for logging before deletion
            user_perm = self.user_perm_repo.get_by_id(user_permission_id)
            if user_perm:
                logger.warning(f"Admin {current_user_id} hard deleting user_permission {user_permission_id} (user {user_perm.user_id}, permission {user_perm.permission_id})")
            
            success = self.user_perm_repo.delete(user_permission_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User permission not found"
                )
            
            return {"message": "User permission deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting user permission {user_permission_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_user_effective_permissions(self, user_id: int, request) -> EffectivePermissionsResponse:
        """Get user's effective permissions (roles + direct)."""
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ Verify token
            
            # Users can view their own permissions, admins can view anyone's
            if current_user_id != user_id:
                self.verify_admin_access(current_user_id)  # ✅ Admin check
            
            # Verify user exists
            self.verify_user_exists(user_id)
            
            # Get effective permissions
            result = self.user_perm_repo.get_user_effective_permissions(user_id)
            
            logger.info(f"Retrieved effective permissions for user {user_id} (requested by user {current_user_id})")
            return EffectivePermissionsResponse(**result)
            
        except ValueError as e:
            logger.warning(f"Error getting effective permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting effective permissions for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def bulk_grant_permissions(self, bulk_data: UserPermissionBulkGrant, request) -> dict:
        """Grant multiple permissions to multiple users."""
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ Verify token
            self.verify_admin_access(current_user_id)  # ✅ Admin only
            
            logger.info(f"Admin {current_user_id} bulk granting {len(bulk_data.permission_ids)} permissions to {len(bulk_data.user_ids)} users")
            
            # Verify all users exist
            from app.apis.auth.models import ExistingUser
            users_count = self.db.query(func.count(ExistingUser.user_id)).filter(
                ExistingUser.user_id.in_(bulk_data.user_ids),
                ExistingUser.is_active == True
            ).scalar()
            
            if users_count != len(bulk_data.user_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some users do not exist or are inactive"
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
            
            # Bulk grant
            granted = self.user_perm_repo.bulk_grant_permissions(
                bulk_data.user_ids,
                bulk_data.permission_ids,
                current_user_id
            )
            
            logger.info(f"Bulk grant completed: {len(granted)} successful, {(len(bulk_data.user_ids) * len(bulk_data.permission_ids)) - len(granted)} duplicates skipped")
            
            return {
                "message": f"Permissions granted successfully",
                "total_attempted": len(bulk_data.user_ids) * len(bulk_data.permission_ids),
                "successfully_granted": len(granted),
                "duplicates_skipped": (len(bulk_data.user_ids) * len(bulk_data.permission_ids)) - len(granted)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error in bulk grant: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def check_user_permission(self, user_id: int, permission_key: str, request) -> dict:
        """Check if a user has a specific permission."""
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ Verify token
            
            # Users can check their own permissions, admins can check anyone's
            if current_user_id != user_id:
                self.verify_admin_access(current_user_id)  # ✅ Admin check
            
            # Verify user exists
            self.verify_user_exists(user_id)
            
            # Check permission
            has_permission = self.user_perm_repo.check_user_has_permission(user_id, permission_key)
            
            logger.debug(f"Permission check: user {user_id}, permission {permission_key}, result={has_permission} (checked by user {current_user_id})")
            
            return {
                "user_id": user_id,
                "permission_key": permission_key,
                "has_permission": has_permission,
                "checked_at": datetime.utcnow().isoformat(),
                "checked_by": current_user_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error checking permission {permission_key} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    




# Add these methods to UserPermissionService:

    
    def grant_extra_permission(self, user_id: int, permission_id: int, request) -> dict:
        """Grant an extra permission to user (adds to role permissions)."""
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Verify user and permission exist
            self.verify_user_exists(user_id)
            self.verify_permission_exists(permission_id)
            
            # Grant extra permission
            user_perm = self.user_perm_repo.grant_extra_permission(
                user_id=user_id,
                permission_id=permission_id,
                granted_by=current_user_id
            )
            
            return {
                "message": "Extra permission granted successfully",
                "user_permission_id": user_perm.user_permission_id,
                "status": user_perm.status.value,
                "user_id": user_id,
                "permission_id": permission_id
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error granting extra permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def revoke_role_permission(self, user_id: int, permission_id: int, request) -> dict:
        """Revoke a permission from user's role permissions."""
        try:
            current_user_id = self.get_current_user_id(request)
            self.verify_admin_access(current_user_id)
            
            # Verify user and permission exist
            self.verify_user_exists(user_id)
            self.verify_permission_exists(permission_id)
            
            # Revoke role permission
            user_perm = self.user_perm_repo.revoke_role_permission(
                user_id=user_id,
                permission_id=permission_id,
                revoked_by=current_user_id
            )
            
            return {
                "message": "Role permission revoked successfully",
                "user_permission_id": user_perm.user_permission_id,
                "status": user_perm.status.value,
                "user_id": user_id,
                "permission_id": permission_id
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error revoking role permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_user_permission_summary(self, user_id: int, request) -> dict:
        """Get detailed summary of user's permissions with status."""
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Users can view their own permissions, admins can view anyone's
            if current_user_id != user_id:
                self.verify_admin_access(current_user_id)
            
            # Verify user exists
            self.verify_user_exists(user_id)
            
            # Get effective permissions with details
            result = self.user_perm_repo.get_user_effective_permissions(user_id)
            
            # Get user's role details
            from app.apis.access_control.roles.models import Role
            from app.apis.auth.models import ExistingUser
            
            user = self.db.query(ExistingUser).filter(
                ExistingUser.user_id == user_id
            ).first()
            
            role_name = None
            if user and user.role_id:
                role = self.db.query(Role).filter(Role.role_id == user.role_id).first()
                role_name = role.role_name if role else None
            
            return {
                "user_id": user_id,
                "full_name": user.full_name if user else None,
                "email": user.email if user else None,
                "role_id": user.role_id if user else None,
                "role_name": role_name,
                "permission_summary": {
                    "role_permissions": result['role_permissions'],
                    "granted_permissions": result['granted_permissions'],
                    "revoked_permissions": result['revoked_permissions'],
                    "effective_permissions": result['effective_permissions']
                },
                "counts": {
                    "role_permissions": len(result['role_permissions']),
                    "granted_permissions": len(result['granted_permissions']),
                    "revoked_permissions": len(result['revoked_permissions']),
                    "effective_permissions": len(result['effective_permissions'])
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting permission summary for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )