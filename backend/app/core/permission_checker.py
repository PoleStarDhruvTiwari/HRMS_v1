# app/core/permission_checker.py
"""
REUSABLE PERMISSION CHECKING UTILITY
Use this in ALL your services to check permissions.
"""

import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PermissionChecker:
    """Utility class for checking user permissions."""
    
    @staticmethod
    def check_permission(db: Session, user_id: int, permission_key: str) -> bool:
        """
        Check if user has a specific permission.
        Returns True if user has permission, False otherwise.
        """
        try:
            # Import here to avoid circular imports
            from app.apis.access_control.user_permissions.repositories import UserPermissionRepository
            
            user_perm_repo = UserPermissionRepository(db)
            return user_perm_repo.check_user_has_permission(user_id, permission_key)
            
        except Exception as e:
            logger.error(f"Error checking permission {permission_key} for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    def check_any_permission(db: Session, user_id: int, permission_keys: List[str]) -> bool:
        """Check if user has ANY of the specified permissions."""
        for permission_key in permission_keys:
            if PermissionChecker.check_permission(db, user_id, permission_key):
                return True
        return False
    
    @staticmethod
    def verify_permission(db: Session, user_id: int, permission_key: str):
        """
        Verify user has permission, otherwise raise 403.
        Use this in your service methods.
        """
        if not PermissionChecker.check_permission(db, user_id, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission_key}"
            )
    
    @staticmethod
    def verify_any_permission(db: Session, user_id: int, permission_keys: List[str]):
        """
        Verify user has ANY of the permissions, otherwise raise 403.
        Useful when multiple permissions allow the same action.
        """
        if not PermissionChecker.check_any_permission(db, user_id, permission_keys):
            permissions_str = ", ".join(permission_keys)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires any of: {permissions_str}"
            )