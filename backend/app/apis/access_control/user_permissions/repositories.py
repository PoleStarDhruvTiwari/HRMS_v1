# app/apis/access_control/user_permissions/repositories.py
"""
Repository for User Permission operations.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, asc, func
from datetime import datetime

from .models import UserPermission
from app.apis.access_control.permissions.models import Permission
from app.apis.auth.models import ExistingUser

logger = logging.getLogger(__name__)





class UserPermissionRepository:
    """Repository for User Permission database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_permission_id: int) -> Optional[UserPermission]:
        """Get user permission by ID."""
        try:
            return self.db.query(UserPermission).options(
                joinedload(UserPermission.user),
                joinedload(UserPermission.permission),
                joinedload(UserPermission.granter)
            ).filter(UserPermission.user_permission_id == user_permission_id).first()
        except Exception as e:
            logger.error(f"Error fetching user permission {user_permission_id}: {str(e)}")
            raise
    
    def get_by_user_and_permission(self, user_id: int, permission_id: int) -> Optional[UserPermission]:
        """Get user permission by user_id and permission_id."""
        try:
            return self.db.query(UserPermission).options(
                joinedload(UserPermission.user),
                joinedload(UserPermission.permission),
                joinedload(UserPermission.granter)
            ).filter(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission_id
            ).first()
        except Exception as e:
            logger.error(f"Error fetching user permission for user {user_id}, permission {permission_id}: {str(e)}")
            raise
    
    def get_user_permissions(self, user_id: int, active_only: bool = True) -> List[UserPermission]:
        """Get all permissions for a user."""
        try:
            query = self.db.query(UserPermission).options(
                joinedload(UserPermission.permission),
                joinedload(UserPermission.granter)
            ).filter(UserPermission.user_id == user_id)
            
            if active_only:
                query = query.filter(UserPermission.revoked_at.is_(None))
            
            return query.order_by(UserPermission.granted_at.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching permissions for user {user_id}: {str(e)}")
            raise
    
    def get_users_with_permission(self, permission_id: int, active_only: bool = True) -> List[UserPermission]:
        """Get all users who have a specific permission."""
        try:
            query = self.db.query(UserPermission).options(
                joinedload(UserPermission.user),
                joinedload(UserPermission.granter)
            ).filter(UserPermission.permission_id == permission_id)
            
            if active_only:
                query = query.filter(UserPermission.revoked_at.is_(None))
            
            return query.order_by(UserPermission.granted_at.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching users with permission {permission_id}: {str(e)}")
            raise
    
    def grant_permission(self, user_id: int, permission_id: int, granted_by: int) -> UserPermission:
        """Grant permission to a user."""
        try:
            # Check if already exists
            existing = self.get_by_user_and_permission(user_id, permission_id)
            
            if existing:
                if existing.revoked_at:
                    # Reactivate revoked permission
                    existing.revoked_at = None
                    existing.granted_by = granted_by
                    existing.granted_at = datetime.utcnow()
                    self.db.commit()
                    self.db.refresh(existing)
                    logger.info(f"Reactivated permission {permission_id} for user {user_id}")
                    return existing
                else:
                    raise ValueError(f"Permission {permission_id} is already granted to user {user_id}")
            
            # Create new user permission
            user_permission = UserPermission(
                user_id=user_id,
                permission_id=permission_id,
                granted_by=granted_by
            )
            
            self.db.add(user_permission)
            self.db.commit()
            self.db.refresh(user_permission)
            
            logger.info(f"Granted permission {permission_id} to user {user_id}")
            return user_permission
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error granting permission {permission_id} to user {user_id}: {str(e)}")
            raise
    
    def revoke_permission(self, user_permission_id: int) -> bool:
        """Revoke a user permission (soft delete)."""
        try:
            user_permission = self.get_by_id(user_permission_id)
            if not user_permission:
                return False
            
            if user_permission.revoked_at:
                return False  # Already revoked
            
            user_permission.revoked_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Revoked user permission {user_permission_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking user permission {user_permission_id}: {str(e)}")
            raise
    
    def revoke_by_user_and_permission(self, user_id: int, permission_id: int) -> bool:
        """Revoke permission from user using user_id and permission_id."""
        try:
            user_permission = self.get_by_user_and_permission(user_id, permission_id)
            if not user_permission or user_permission.revoked_at:
                return False
            
            user_permission.revoked_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Revoked permission {permission_id} from user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking permission {permission_id} from user {user_id}: {str(e)}")
            raise
    
    def delete(self, user_permission_id: int) -> bool:
        """Hard delete a user permission record."""
        try:
            user_permission = self.get_by_id(user_permission_id)
            if not user_permission:
                return False
            
            self.db.delete(user_permission)
            self.db.commit()
            
            logger.warning(f"Hard deleted user permission {user_permission_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user permission {user_permission_id}: {str(e)}")
            raise
    

    def check_user_has_permission(self, user_id: int, permission_key: str) -> bool:
        """
        MINIMAL CODE CHANGE VERSION:
        Check if user has permission considering role permissions and user overrides.
        """
        try:
            # Get permission ID
            permission = self.db.query(Permission).filter(
                Permission.permission_key == permission_key,
                Permission.status == 'active'
            ).first()
            
            if not permission:
                return False
            
            permission_id = permission.permission_id
            
            # Check user's direct permission override
            user_perm = self.db.query(UserPermission).filter(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission_id
            ).first()
            
            if user_perm:
                # User has explicit permission record
                return user_perm.status == 'granted'  # Only true if status is 'granted'
            
            # If no user permission override, check role permission
            from app.apis.access_control.role_permissions.models import  RolePermission
            from app.apis.auth.models import ExistingUser as UserRole
            
            has_role_permission = self.db.query(UserRole).join(
                RolePermission, UserRole.role_id == RolePermission.role_id
            ).filter(
                UserRole.user_id == user_id,
                RolePermission.permission_id == permission_id
            ).first()
            
            return has_role_permission is not None
            
        except Exception as e:
            logger.error(f"Error checking permission {permission_key} for user {user_id}: {str(e)}")
            return False
    
    def get_user_effective_permissions(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's effective permissions (with role and user overrides).
        """
        try:
            # Get user details
            user = self.db.query(ExistingUser).filter(
                ExistingUser.user_id == user_id
            ).first()
            
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # 1. Get role permissions
            role_permission_keys = set()
            if user.role_id:
                from app.apis.access_control.roles.models import RolePermission
                
                role_perms = self.db.query(RolePermission).join(
                    Permission, RolePermission.permission_id == Permission.permission_id
                ).filter(
                    RolePermission.role_id == user.role_id,
                    Permission.status == 'active'
                ).all()
                
                for rp in role_perms:
                    if rp.permission and rp.permission.permission_key:
                        role_permission_keys.add(rp.permission.permission_key)
            
            # 2. Get user's granted permissions (extra permissions)
            granted_perms = self.get_granted_permissions(user_id)
            granted_permission_keys = set()
            for up in granted_perms:
                if up.permission and up.permission.permission_key:
                    granted_permission_keys.add(up.permission.permission_key)
            
            # 3. Get user's revoked permissions (removed from role)
            revoked_perms = self.get_revoked_permissions(user_id)
            revoked_permission_keys = set()
            for up in revoked_perms:
                if up.permission and up.permission.permission_key:
                    revoked_permission_keys.add(up.permission.permission_key)
            
            # 4. Calculate final permissions:
            # (role_permissions + granted_permissions) - revoked_permissions
            base_permissions = role_permission_keys.union(granted_permission_keys)
            final_permissions = base_permissions - revoked_permission_keys
            
            return {
                'user_id': user_id,
                'full_name': user.full_name,
                'email': user.email,
                'role_id': user.role_id,
                'role_permissions': sorted(role_permission_keys),
                'granted_permissions': sorted(granted_permission_keys),
                'revoked_permissions': sorted(revoked_permission_keys),
                'effective_permissions': sorted(final_permissions),
                'total_effective': len(final_permissions)
            }
            
        except Exception as e:
            logger.error(f"Error getting effective permissions for user {user_id}: {str(e)}")
            raise















    # def get_user_effective_permissions(self, user_id: int) -> Dict[str, Any]:
    #     """
    #     Get user's effective permissions (roles + direct permissions).
    #     Returns combined unique permissions.
    #     """
    #     try:
    #         # Get user details
    #         user = self.db.query(ExistingUser).filter(
    #             ExistingUser.user_id == user_id
    #         ).first()
            
    #         if not user:
    #             raise ValueError(f"User {user_id} not found")
            
    #         # Get direct permissions
    #         direct_perms = self.get_user_permissions(user_id, active_only=True)
    #         direct_permission_keys = set()
            
    #         for up in direct_perms:
    #             if up.permission and up.permission.permission_key:
    #                 direct_permission_keys.add(up.permission.permission_key)
            
    #         # Get role permissions
    #         role_permission_keys = set()
    #         if user.roles:
    #             for role in user.roles:
    #                 if hasattr(role, 'permissions'):
    #                     for rp in role.permissions:
    #                         if rp.permission and rp.permission.permission_key:
    #                             role_permission_keys.add(rp.permission.permission_key)
            
    #         # Combine and deduplicate
    #         all_permission_keys = direct_permission_keys.union(role_permission_keys)
            
    #         return {
    #             'user_id': user_id,
    #             'full_name': user.full_name,
    #             'email': user.email,
    #             'direct_permissions': list(direct_permission_keys),
    #             'role_permissions': list(role_permission_keys),
    #             'all_permissions': sorted(all_permission_keys),
    #             'total_permissions': len(all_permission_keys)
    #         }
            
    #     except Exception as e:
    #         logger.error(f"Error getting effective permissions for user {user_id}: {str(e)}")
    #         raise
    
    # def check_user_has_permission(self, user_id: int, permission_key: str) -> bool:
    #     """Check if user has a specific permission (directly or via roles)."""
    #     try:
    #         # Check direct permissions
    #         direct_has = self.db.query(UserPermission).join(
    #             Permission, UserPermission.permission_id == Permission.permission_id
    #         ).filter(
    #             UserPermission.user_id == user_id,
    #             UserPermission.revoked_at.is_(None),
    #             Permission.permission_key == permission_key
    #         ).first()
            
    #         if direct_has:
    #             return True
            
    #         # Check role permissions
    #         from app.apis.access_control.roles.models import UserRole, RolePermission
            
    #         role_has = self.db.query(UserRole).join(
    #             RolePermission, UserRole.role_id == RolePermission.role_id
    #         ).join(
    #             Permission, RolePermission.permission_id == Permission.permission_id
    #         ).filter(
    #             UserRole.user_id == user_id,
    #             Permission.permission_key == permission_key
    #         ).first()
            
    #         return role_has is not None
            
    #     except Exception as e:
    #         logger.error(f"Error checking permission {permission_key} for user {user_id}: {str(e)}")
    #         return False
    
    def search_user_permissions(self, user_id: Optional[int] = None, 
                               permission_key: Optional[str] = None,
                               active_only: bool = True,
                               skip: int = 0, limit: int = 100) -> Tuple[List[UserPermission], int]:
        """Search user permissions with filters."""
        try:
            query = self.db.query(UserPermission).options(
                joinedload(UserPermission.user),
                joinedload(UserPermission.permission),
                joinedload(UserPermission.granter)
            )
            
            if user_id:
                query = query.filter(UserPermission.user_id == user_id)
            
            if permission_key:
                query = query.join(Permission).filter(
                    Permission.permission_key.ilike(f"%{permission_key}%")
                )
            
            if active_only:
                query = query.filter(UserPermission.revoked_at.is_(None))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            results = query.order_by(
                UserPermission.granted_at.desc()
            ).offset(skip).limit(limit).all()
            
            return results, total
            
        except Exception as e:
            logger.error(f"Error searching user permissions: {str(e)}")
            raise
    
    def bulk_grant_permissions(self, user_ids: List[int], 
                              permission_ids: List[int], 
                              granted_by: int) -> List[UserPermission]:
        """Grant multiple permissions to multiple users."""
        try:
            granted = []
            for user_id in user_ids:
                for permission_id in permission_ids:
                    try:
                        user_perm = self.grant_permission(user_id, permission_id, granted_by)
                        granted.append(user_perm)
                    except ValueError as e:
                        # Skip if already granted
                        logger.warning(f"Skipping duplicate: {str(e)}")
                        continue
            
            return granted
            
        except Exception as e:
            logger.error(f"Error in bulk grant: {str(e)}")
            raise


# app/apis/access_control/user_permissions/repositories.py
# Add/update these methods:
    # ... existing code ...
    
    def get_user_permissions_with_status(self, user_id: int) -> List[UserPermission]:
        """Get all user permissions with their status."""
        try:
            return self.db.query(UserPermission).options(
                joinedload(UserPermission.permission),
                joinedload(UserPermission.updater)
            ).filter(UserPermission.user_id == user_id).all()
        except Exception as e:
            logger.error(f"Error fetching permissions for user {user_id}: {str(e)}")
            raise
    
    def get_granted_permissions(self, user_id: int) -> List[UserPermission]:
        """Get permissions granted extra to user."""
        try:
            return self.db.query(UserPermission).options(
                joinedload(UserPermission.permission)
            ).filter(
                UserPermission.user_id == user_id,
                UserPermission.status == UserPermissionStatus.GRANTED
            ).all()
        except Exception as e:
            logger.error(f"Error fetching granted permissions for user {user_id}: {str(e)}")
            raise
    
    def get_revoked_permissions(self, user_id: int) -> List[UserPermission]:
        """Get permissions revoked from user's role."""
        try:
            return self.db.query(UserPermission).options(
                joinedload(UserPermission.permission)
            ).filter(
                UserPermission.user_id == user_id,
                UserPermission.status == UserPermissionStatus.REVOKED
            ).all()
        except Exception as e:
            logger.error(f"Error fetching revoked permissions for user {user_id}: {str(e)}")
            raise
    
    def grant_extra_permission(self, user_id: int, permission_id: int, granted_by: int) -> UserPermission:
        """Grant an extra permission to user (adds to role permissions)."""
        try:
            # Check if already exists
            existing = self.get_by_user_and_permission(user_id, permission_id)
            
            if existing:
                if existing.status == UserPermissionStatus.REVOKED:
                    # Change from revoked to granted
                    existing.status = UserPermissionStatus.GRANTED
                    existing.updated_by = granted_by
                    self.db.commit()
                    self.db.refresh(existing)
                    logger.info(f"Changed revoked permission {permission_id} to granted for user {user_id}")
                    return existing
                elif existing.status == UserPermissionStatus.GRANTED:
                    raise ValueError(f"Permission {permission_id} is already granted to user {user_id}")
            
            # Create new granted permission
            user_permission = UserPermission(
                user_id=user_id,
                permission_id=permission_id,
                status=UserPermissionStatus.GRANTED,
                updated_by=granted_by
            )
            
            self.db.add(user_permission)
            self.db.commit()
            self.db.refresh(user_permission)
            
            logger.info(f"Granted extra permission {permission_id} to user {user_id}")
            return user_permission
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error granting extra permission {permission_id} to user {user_id}: {str(e)}")
            raise
    
    def revoke_role_permission(self, user_id: int, permission_id: int, revoked_by: int) -> UserPermission:
        """Revoke a permission from user's role permissions."""
        try:
            # Check if already exists
            existing = self.get_by_user_and_permission(user_id, permission_id)
            
            if existing:
                if existing.status == UserPermissionStatus.GRANTED:
                    # Change from granted to revoked
                    existing.status = UserPermissionStatus.REVOKED
                    existing.updated_by = revoked_by
                    self.db.commit()
                    self.db.refresh(existing)
                    logger.info(f"Changed granted permission {permission_id} to revoked for user {user_id}")
                    return existing
                elif existing.status == UserPermissionStatus.REVOKED:
                    raise ValueError(f"Permission {permission_id} is already revoked from user {user_id}")
            
            # Create new revoked permission
            user_permission = UserPermission(
                user_id=user_id,
                permission_id=permission_id,
                status=UserPermissionStatus.REVOKED,
                updated_by=revoked_by
            )
            
            self.db.add(user_permission)
            self.db.commit()
            self.db.refresh(user_permission)
            
            logger.info(f"Revoked role permission {permission_id} from user {user_id}")
            return user_permission
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking permission {permission_id} from user {user_id}: {str(e)}")
            raise
    
    def remove_user_permission(self, user_id: int, permission_id: int) -> bool:
        """Remove a user permission record (both granted and revoked)."""
        try:
            user_permission = self.get_by_user_and_permission(user_id, permission_id)
            if not user_permission:
                return False
            
            self.db.delete(user_permission)
            self.db.commit()
            
            logger.info(f"Removed user permission {permission_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing permission {permission_id} from user {user_id}: {str(e)}")
            raise