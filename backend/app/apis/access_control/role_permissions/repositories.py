# app/apis/access_control/role_permissions/repositories.py
"""
Repository for Role Permission operations.
"""

import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from .models import RolePermission
from app.apis.access_control.roles.models import Role
from app.apis.access_control.permissions.models import Permission

logger = logging.getLogger(__name__)


class RolePermissionRepository:
    """Repository for Role Permission database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, role_permission_id: int) -> Optional[RolePermission]:
        """Get role permission by ID."""
        try:
            return self.db.query(RolePermission).options(
                joinedload(RolePermission.role),
                joinedload(RolePermission.permission),
                joinedload(RolePermission.updater)
            ).filter(RolePermission.role_permission_id == role_permission_id).first()
        except Exception as e:
            logger.error(f"Error fetching role permission {role_permission_id}: {str(e)}")
            raise
    
    def get_by_role_and_permission(self, role_id: int, permission_id: int) -> Optional[RolePermission]:
        """Get role permission by role_id and permission_id."""
        try:
            return self.db.query(RolePermission).options(
                joinedload(RolePermission.role),
                joinedload(RolePermission.permission),
                joinedload(RolePermission.updater)
            ).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            ).first()
        except Exception as e:
            logger.error(f"Error fetching role permission for role {role_id}, permission {permission_id}: {str(e)}")
            raise
    
    def get_role_permissions(self, role_id: int) -> List[RolePermission]:
        """Get all permissions for a role."""
        try:
            return self.db.query(RolePermission).options(
                joinedload(RolePermission.permission),
                joinedload(RolePermission.updater)
            ).filter(RolePermission.role_id == role_id).order_by(
                RolePermission.updated_at.desc()
            ).all()
        except Exception as e:
            logger.error(f"Error fetching permissions for role {role_id}: {str(e)}")
            raise
    
    def get_roles_with_permission(self, permission_id: int) -> List[RolePermission]:
        """Get all roles that have a specific permission."""
        try:
            return self.db.query(RolePermission).options(
                joinedload(RolePermission.role),
                joinedload(RolePermission.updater)
            ).filter(RolePermission.permission_id == permission_id).order_by(
                RolePermission.updated_at.desc()
            ).all()
        except Exception as e:
            logger.error(f"Error fetching roles with permission {permission_id}: {str(e)}")
            raise
    
    def assign_permission(self, role_id: int, permission_id: int, updated_by: int) -> RolePermission:
        """Assign permission to role."""
        try:
            # Check if already exists
            existing = self.get_by_role_and_permission(role_id, permission_id)
            if existing:
                # Update existing record
                existing.updated_by = updated_by
                self.db.commit()
                self.db.refresh(existing)
                logger.info(f"Updated role permission {role_id}, {permission_id}")
                return existing
            
            # Create new role permission
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                updated_by=updated_by
            )
            
            self.db.add(role_permission)
            self.db.commit()
            self.db.refresh(role_permission)
            
            logger.info(f"Assigned permission {permission_id} to role {role_id}")
            return role_permission
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error assigning permission {permission_id} to role {role_id}: {str(e)}")
            raise
    
    def remove_permission(self, role_permission_id: int) -> bool:
        """Remove permission from role."""
        try:
            role_permission = self.get_by_id(role_permission_id)
            if not role_permission:
                return False
            
            self.db.delete(role_permission)
            self.db.commit()
            
            logger.info(f"Removed role permission {role_permission_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing role permission {role_permission_id}: {str(e)}")
            raise
    
    def remove_by_role_and_permission(self, role_id: int, permission_id: int) -> bool:
        """Remove permission from role using role_id and permission_id."""
        try:
            role_permission = self.get_by_role_and_permission(role_id, permission_id)
            if not role_permission:
                return False
            
            self.db.delete(role_permission)
            self.db.commit()
            
            logger.info(f"Removed permission {permission_id} from role {role_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing permission {permission_id} from role {role_id}: {str(e)}")
            raise
    
    def get_role_permission_keys(self, role_id: int) -> List[str]:
        """Get permission keys for a role."""
        try:
            permissions = self.db.query(Permission.permission_key).join(
                RolePermission, Permission.permission_id == RolePermission.permission_id
            ).filter(
                RolePermission.role_id == role_id,
                Permission.status == 'active'
            ).all()
            
            return [p[0] for p in permissions]
        except Exception as e:
            logger.error(f"Error getting permission keys for role {role_id}: {str(e)}")
            return []
    
    def check_role_has_permission(self, role_id: int, permission_key: str) -> bool:
        """Check if role has a specific permission."""
        try:
            result = self.db.query(RolePermission).join(
                Permission, RolePermission.permission_id == Permission.permission_id
            ).filter(
                RolePermission.role_id == role_id,
                Permission.permission_key == permission_key,
                Permission.status == 'active'
            ).first()
            
            return result is not None
        except Exception as e:
            logger.error(f"Error checking permission {permission_key} for role {role_id}: {str(e)}")
            return False
    
    def bulk_assign_permissions(self, role_ids: List[int], permission_ids: List[int], updated_by: int) -> List[RolePermission]:
        """Assign multiple permissions to multiple roles in bulk."""
        try:
            assigned = []
            for role_id in role_ids:
                for permission_id in permission_ids:
                    try:
                        role_perm = self.assign_permission(role_id, permission_id, updated_by)
                        assigned.append(role_perm)
                    except Exception as e:
                        logger.warning(f"Skipping role {role_id}, permission {permission_id}: {str(e)}")
                        continue
            
            return assigned
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in bulk assign: {str(e)}")
            raise
    
    def search_role_permissions(self, role_id: Optional[int] = None, 
                               permission_key: Optional[str] = None,
                               skip: int = 0, limit: int = 100) -> Tuple[List[RolePermission], int]:
        """Search role permissions with filters."""
        try:
            query = self.db.query(RolePermission).options(
                joinedload(RolePermission.role),
                joinedload(RolePermission.permission),
                joinedload(RolePermission.updater)
            )
            
            if role_id:
                query = query.filter(RolePermission.role_id == role_id)
            
            if permission_key:
                query = query.join(Permission).filter(
                    Permission.permission_key.ilike(f"%{permission_key}%")
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            results = query.order_by(
                RolePermission.updated_at.desc()
            ).offset(skip).limit(limit).all()
            
            return results, total
            
        except Exception as e:
            logger.error(f"Error searching role permissions: {str(e)}")
            raise
    
    def get_count(self, role_id: Optional[int] = None) -> int:
        """Get total role permission count."""
        try:
            query = self.db.query(func.count(RolePermission.role_permission_id))
            
            if role_id:
                query = query.filter(RolePermission.role_id == role_id)
            
            count = query.scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting role permission count: {str(e)}")
            raise