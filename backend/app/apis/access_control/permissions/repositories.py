# app/apis/access_control/permissions/repositories.py
"""
Repository for READ-ONLY permission operations.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from .models import Permission

logger = logging.getLogger(__name__)


class PermissionRepository:
    """Repository for Permission READ-ONLY database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, permission_id: int) -> Optional[Permission]:
        """Get permission by ID."""
        logger.debug(f"Fetching permission by ID: {permission_id}")
        try:
            permission = self.db.query(Permission).options(
                joinedload(Permission.updater)
            ).filter(Permission.permission_id == permission_id).first()
            return permission
        except Exception as e:
            logger.error(f"Error fetching permission by ID {permission_id}: {str(e)}")
            raise
    
    def get_by_key(self, permission_key: str) -> Optional[Permission]:
        """Get permission by key."""
        logger.debug(f"Fetching permission by key: {permission_key}")
        try:
            permission = self.db.query(Permission).options(
                joinedload(Permission.updater)
            ).filter(Permission.permission_key == permission_key).first()
            return permission
        except Exception as e:
            logger.error(f"Error fetching permission by key {permission_key}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Permission]:
        """Get all permissions with pagination."""
        logger.debug(f"Fetching all permissions (skip: {skip}, limit: {limit}, active_only: {active_only})")
        try:
            query = self.db.query(Permission).options(
                joinedload(Permission.updater)
            )
            
            if active_only:
                query = query.filter(Permission.status == 'active')
            
            permissions = query.order_by(Permission.permission_key).offset(skip).limit(limit).all()
            return permissions
        except Exception as e:
            logger.error(f"Error fetching all permissions: {str(e)}")
            raise
    
    def search(self, search_term: str = None, active_only: bool = True, 
               skip: int = 0, limit: int = 100) -> Tuple[List[Permission], int]:
        """Search permissions by key or description."""
        logger.debug(f"Searching permissions: {search_term}")
        
        try:
            query = self.db.query(Permission).options(
                joinedload(Permission.updater)
            )
            
            if active_only:
                query = query.filter(Permission.status == 'active')
            
            if search_term:
                search = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Permission.permission_key.ilike(search),
                        Permission.description.ilike(search)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            permissions = query.order_by(Permission.permission_key).offset(skip).limit(limit).all()
            
            return permissions, total
            
        except Exception as e:
            logger.error(f"Error searching permissions: {str(e)}")
            raise
    
    def get_by_module(self, module: str, active_only: bool = True) -> List[Permission]:
        """Get permissions by module prefix."""
        logger.debug(f"Getting permissions for module: {module}")
        
        try:
            query = self.db.query(Permission).options(
                joinedload(Permission.updater)
            ).filter(
                Permission.permission_key.startswith(f"{module}.")
            )
            
            if active_only:
                query = query.filter(Permission.status == 'active')
            
            permissions = query.order_by(Permission.permission_key).all()
            return permissions
        except Exception as e:
            logger.error(f"Error getting permissions by module {module}: {str(e)}")
            raise
    
    def get_role_count(self, permission_id: int) -> int:
        """Get number of roles with this permission."""
        logger.debug(f"Getting role count for permission: {permission_id}")
        
        try:
            from app.apis.access_control.roles.models import RolePermission
            count = self.db.query(func.count(RolePermission.role_id)).filter(
                RolePermission.permission_id == permission_id
            ).scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Error getting role count for permission {permission_id}: {str(e)}")
            return 0
    
    def get_permissions_with_role_counts(self, skip: int = 0, limit: int = 100, 
                                        active_only: bool = True) -> List[Tuple[Permission, int]]:
        """Get permissions with their role counts."""
        logger.debug(f"Getting permissions with role counts")
        
        try:
            # Get all permissions
            permissions = self.get_all(skip=skip, limit=limit, active_only=active_only)
            
            # Get role counts for each permission
            permissions_with_counts = []
            for permission in permissions:
                count = self.get_role_count(permission.permission_id)
                permissions_with_counts.append((permission, count))
            
            return permissions_with_counts
            
        except Exception as e:
            logger.error(f"Error getting permissions with role counts: {str(e)}")
            raise
    
    def get_count(self, active_only: bool = True) -> int:
        """Get total permission count."""
        logger.debug(f"Getting permission count (active_only: {active_only})")
        try:
            query = self.db.query(func.count(Permission.permission_id))
            
            if active_only:
                query = query.filter(Permission.status == 'active')
            
            count = query.scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting permission count: {str(e)}")
            raise