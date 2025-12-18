# app/apis/roles/repositories.py
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func

from .models import Role
from .schemas import RoleFilter

logger = logging.getLogger(__name__)


class RoleRepository:
    """Repository for Role database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        logger.debug(f"Fetching role by ID: {role_id}")
        try:
            role = self.db.query(Role).filter(Role.role_id == role_id).first()
            if role:
                logger.debug(f"Role found: {role.role_code}")
            else:
                logger.debug(f"No role found with ID: {role_id}")
            return role
        except Exception as e:
            logger.error(f"Error fetching role by ID {role_id}: {str(e)}")
            raise
    
    def get_by_code(self, role_code: str) -> Optional[Role]:
        """Get role by code."""
        logger.debug(f"Fetching role by code: {role_code}")
        try:
            role = self.db.query(Role).filter(Role.role_code == role_code.upper()).first()
            return role
        except Exception as e:
            logger.error(f"Error fetching role by code {role_code}: {str(e)}")
            raise
    
    def get_by_name(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        logger.debug(f"Fetching role by name: {role_name}")
        try:
            role = self.db.query(Role).filter(Role.role_name == role_name).first()
            return role
        except Exception as e:
            logger.error(f"Error fetching role by name {role_name}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Get all roles with pagination."""
        logger.debug(f"Fetching all roles (skip: {skip}, limit: {limit})")
        try:
            roles = self.db.query(Role).offset(skip).limit(limit).all()
            logger.debug(f"Found {len(roles)} roles")
            return roles
        except Exception as e:
            logger.error(f"Error fetching all roles: {str(e)}")
            raise
    
    def search_roles(self, filters: RoleFilter, skip: int = 0, limit: int = 100,
                    sort_by: str = "role_code", sort_order: str = "asc") -> Tuple[List[Role], int]:
        """Search roles with filters."""
        logger.debug(f"Searching roles with filters: {filters.dict(exclude_none=True)}")
        
        try:
            query = self.db.query(Role)
            
            # Apply filters
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Role.role_code.ilike(search_term),
                        Role.role_name.ilike(search_term),
                        Role.description.ilike(search_term)
                    )
                )
            
            if filters.role_code:
                query = query.filter(Role.role_code.ilike(f"%{filters.role_code}%"))
            
            if filters.role_name:
                query = query.filter(Role.role_name.ilike(f"%{filters.role_name}%"))
            
            # Get total count before pagination
            total = query.count()
            
            # Apply sorting
            sort_column = getattr(Role, sort_by, Role.role_code)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            roles = query.offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(roles)} roles (total: {total})")
            return roles, total
            
        except Exception as e:
            logger.error(f"Error searching roles: {str(e)}")
            raise
    
    def create(self, role_data: Dict[str, Any], updated_by_id: int) -> Role:
        """Create a new role."""
        logger.info(f"Creating new role: {role_data.get('role_code')}")
        
        try:
            # Check if role_code already exists
            existing_code = self.get_by_code(role_data['role_code'])
            if existing_code:
                raise ValueError(f"Role code already exists: {role_data['role_code']}")
            
            # Check if role_name already exists
            existing_name = self.get_by_name(role_data['role_name'])
            if existing_name:
                raise ValueError(f"Role name already exists: {role_data['role_name']}")
            
            # Create role object
            role = Role(**role_data)
            role.updated_by_id = updated_by_id
            
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
            
            logger.info(f"Role created successfully: {role.role_code} (ID: {role.role_id})")
            return role
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating role: {str(e)}")
            raise
    
    def update(self, role: Role, update_data: Dict[str, Any], updated_by_id: int) -> Role:
        """Update an existing role."""
        logger.debug(f"Updating role: {role.role_code} (ID: {role.role_id})")
        
        try:
            # Check for duplicate role_code if being changed
            if 'role_code' in update_data and update_data['role_code'] != role.role_code:
                existing_code = self.get_by_code(update_data['role_code'])
                if existing_code and existing_code.role_id != role.role_id:
                    raise ValueError(f"Role code already exists: {update_data['role_code']}")
            
            # Check for duplicate role_name if being changed
            if 'role_name' in update_data and update_data['role_name'] != role.role_name:
                existing_name = self.get_by_name(update_data['role_name'])
                if existing_name and existing_name.role_id != role.role_id:
                    raise ValueError(f"Role name already exists: {update_data['role_name']}")
            
            # Update fields
            for key, value in update_data.items():
                if value is not None and hasattr(role, key):
                    setattr(role, key, value)
            
            # Update metadata
            role.updated_by_id = updated_by_id
            role.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(role)
            
            logger.debug(f"Role updated successfully: {role.role_code}")
            return role
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating role {role.role_id}: {str(e)}")
            raise
    
    def delete(self, role_id: int) -> bool:
        """Delete a role."""
        logger.warning(f"Deleting role: {role_id}")
        
        try:
            role = self.get_by_id(role_id)
            if not role:
                logger.warning(f"Role not found for deletion: {role_id}")
                return False
            
            # Check if role is being used by users
            from app.apis.users.models import User
            user_count = self.db.query(User).filter(User.role_id == role_id).count()
            if user_count > 0:
                raise ValueError(f"Cannot delete role {role.role_code}. It is assigned to {user_count} user(s).")
            
            self.db.delete(role)
            self.db.commit()
            
            logger.warning(f"Role deleted successfully: {role_id}")
            return True
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting role {role_id}: {str(e)}")
            raise
    
    def bulk_update(self, role_ids: List[int], update_data: Dict[str, Any], updated_by_id: int) -> int:
        """Update multiple roles at once."""
        logger.info(f"Bulk updating {len(role_ids)} roles")
        
        try:
            # Filter out None values
            update_fields = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_fields:
                logger.warning("No valid fields to update")
                return 0
            
            # Add metadata
            update_fields['updated_by_id'] = updated_by_id
            update_fields['updated_at'] = datetime.utcnow()
            
            # Perform bulk update
            result = self.db.query(Role).filter(Role.role_id.in_(role_ids)).update(
                update_fields,
                synchronize_session=False
            )
            
            self.db.commit()
            logger.info(f"Bulk update completed: {result} roles updated")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in bulk update: {str(e)}")
            raise
    
    def get_role_counts(self) -> Dict[str, int]:
        """Get role statistics."""
        logger.debug("Getting role counts")
        
        try:
            counts = {}
            
            # Total roles
            counts['total'] = self.db.query(func.count(Role.role_id)).scalar()
            
            # Roles with description
            counts['with_description'] = self.db.query(func.count(Role.role_id)).filter(
                Role.description.isnot(None)
            ).scalar()
            
            # Roles without description
            counts['without_description'] = counts['total'] - counts['with_description']
            
            logger.debug(f"Role counts: {counts}")
            return counts
            
        except Exception as e:
            logger.error(f"Error getting role counts: {str(e)}")
            raise
    
    def get_roles_by_ids(self, role_ids: List[int]) -> List[Role]:
        """Get multiple roles by IDs."""
        logger.debug(f"Fetching {len(role_ids)} roles by IDs")
        
        try:
            roles = self.db.query(Role).filter(Role.role_id.in_(role_ids)).all()
            logger.debug(f"Found {len(roles)} roles")
            return roles
        except Exception as e:
            logger.error(f"Error fetching roles by IDs: {str(e)}")
            raise