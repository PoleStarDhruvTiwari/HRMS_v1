# app/core/base_service.py
"""
Base service class with common functionality.
All your services should inherit from this.
"""

import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import security_service
from app.core.permission_checker import PermissionChecker

logger = logging.getLogger(__name__)


class BaseService:
    """Base service with common methods."""
    
    def __init__(self, db: Session):
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
            
            return user_id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    def verify_permission(self, user_id: int, permission_key: str):
        """Verify user has permission."""
        PermissionChecker.verify_permission(self.db, user_id, permission_key)
    
    def verify_any_permission(self, user_id: int, permission_keys: list):
        """Verify user has any of the permissions."""
        PermissionChecker.verify_any_permission(self.db, user_id, permission_keys)