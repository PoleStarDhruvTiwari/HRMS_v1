# app/apis/users/repositories.py
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func

from .models import User
from .schemas import UserFilter

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        logger.debug(f"Fetching user by ID: {user_id}")
        try:
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if user:
                logger.debug(f"User found: {user.email}")
            else:
                logger.debug(f"No user found with ID: {user_id}")
            return user
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {str(e)}")
            raise
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        logger.debug(f"Fetching user by email: {email}")
        try:
            user = self.db.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        logger.debug(f"Fetching all users (skip: {skip}, limit: {limit})")
        try:
            users = self.db.query(User).offset(skip).limit(limit).all()
            logger.debug(f"Found {len(users)} users")
            return users
        except Exception as e:
            logger.error(f"Error fetching all users: {str(e)}")
            raise
    
    def search_users(self, filters: UserFilter, skip: int = 0, limit: int = 100, 
                    sort_by: str = "user_id", sort_order: str = "asc") -> Tuple[List[User], int]:
        """Search users with filters, sorting, and pagination."""
        logger.debug(f"Searching users with filters: {filters.dict(exclude_none=True)}")
        
        try:
            query = self.db.query(User)
            
            # Apply filters
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        User.full_name.ilike(search_term),
                        User.email.ilike(search_term),
                        User.global_employee_id.ilike(search_term),
                        User.phone_number.ilike(search_term)
                    )
                )
            
            if filters.status:
                query = query.filter(User.status == filters.status.value)
            
            if filters.team_id is not None:
                query = query.filter(User.team_id == filters.team_id)
            
            if filters.vertical_id is not None:
                query = query.filter(User.vertical_id == filters.vertical_id)
            
            if filters.designation_id is not None:
                query = query.filter(User.designation_id == filters.designation_id)
            
            if filters.role_id is not None:
                query = query.filter(User.role_id == filters.role_id)
            
            if filters.is_active is not None:
                query = query.filter(User.is_active == filters.is_active)
            
            if filters.is_admin is not None:
                query = query.filter(User.is_admin == filters.is_admin)
            
            if filters.date_of_joining_from:
                query = query.filter(User.date_of_joining >= filters.date_of_joining_from)
            
            if filters.date_of_joining_to:
                query = query.filter(User.date_of_joining <= filters.date_of_joining_to)
            
            # Get total count before pagination
            total = query.count()
            
            # Apply sorting
            sort_column = getattr(User, sort_by, User.user_id)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            users = query.offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(users)} users (total: {total})")
            return users, total
            
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise
    
    def create(self, user_data: Dict[str, Any], created_by: int) -> User:
        """Create a new user."""
        logger.info(f"Creating new user: {user_data.get('email')}")
        
        try:
            # Create user object
            user = User(**user_data)
            user.updated_by = created_by
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User created successfully: {user.email} (ID: {user.user_id})")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    def update(self, user: User, update_data: Dict[str, Any], updated_by: int) -> User:
        """Update an existing user."""
        logger.debug(f"Updating user: {user.email} (ID: {user.user_id})")
        
        try:
            # Update fields
            for key, value in update_data.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
            
            # Update metadata
            user.updated_by = updated_by
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.debug(f"User updated successfully: {user.email}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user.user_id}: {str(e)}")
            raise
    
    def bulk_update(self, user_ids: List[int], update_data: Dict[str, Any], updated_by: int) -> int:
        """Update multiple users at once."""
        logger.info(f"Bulk updating {len(user_ids)} users")
        
        try:
            # Filter out None values
            update_fields = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_fields:
                logger.warning("No valid fields to update")
                return 0
            
            # Add metadata
            update_fields['updated_by'] = updated_by
            update_fields['updated_at'] = datetime.utcnow()
            
            # Perform bulk update
            result = self.db.query(User).filter(User.user_id.in_(user_ids)).update(
                update_fields,
                synchronize_session=False
            )
            
            self.db.commit()
            logger.info(f"Bulk update completed: {result} users updated")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in bulk update: {str(e)}")
            raise
    
    def delete(self, user_id: int) -> bool:
        """Delete a user."""
        logger.warning(f"Deleting user: {user_id}")
        
        try:
            user = self.get_by_id(user_id)
            if not user:
                logger.warning(f"User not found for deletion: {user_id}")
                return False
            
            self.db.delete(user)
            self.db.commit()
            
            logger.warning(f"User deleted successfully: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise
    
    def update_last_login(self, user_id: int) -> Optional[User]:
        """Update user's last login timestamp."""
        logger.debug(f"Updating last login for user: {user_id}")
        
        try:
            user = self.get_by_id(user_id)
            if user:
                user.last_login = datetime.utcnow()
                self.db.commit()
                self.db.refresh(user)
                logger.debug(f"Last login updated for user: {user_id}")
            else:
                logger.warning(f"User not found for last login update: {user_id}")
            
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating last login for user {user_id}: {str(e)}")
            raise
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile with related data."""
        logger.debug(f"Fetching profile for user: {user_id}")
        
        try:
            user = self.get_by_id(user_id)
            if not user:
                return None
            
            # Get reporting manager names
            reporting_level1_name = None
            reporting_level2_name = None
            updater_name = None
            
            if user.reporting_level1_id:
                manager1 = self.get_by_id(user.reporting_level1_id)
                reporting_level1_name = manager1.full_name if manager1 else None
            
            if user.reporting_level2_id:
                manager2 = self.get_by_id(user.reporting_level2_id)
                reporting_level2_name = manager2.full_name if manager2 else None
            
            if user.updated_by:
                updater = self.get_by_id(user.updated_by)
                updater_name = updater.full_name if updater else None
            
            return {
                "user": user,
                "reporting_level1_name": reporting_level1_name,
                "reporting_level2_name": reporting_level2_name,
                "updater_name": updater_name
            }
            
        except Exception as e:
            logger.error(f"Error fetching user profile {user_id}: {str(e)}")
            raise
    
    def get_users_by_ids(self, user_ids: List[int]) -> List[User]:
        """Get multiple users by IDs."""
        logger.debug(f"Fetching {len(user_ids)} users by IDs")
        
        try:
            users = self.db.query(User).filter(User.user_id.in_(user_ids)).all()
            logger.debug(f"Found {len(users)} users")
            return users
        except Exception as e:
            logger.error(f"Error fetching users by IDs: {str(e)}")
            raise
    
    def get_user_count(self, filters: Optional[UserFilter] = None) -> Dict[str, int]:
        """Get user counts by different criteria."""
        logger.debug("Getting user counts")
        
        try:
            counts = {}
            
            # Total users
            counts['total'] = self.db.query(func.count(User.user_id)).scalar()
            
            # Active users
            counts['active'] = self.db.query(func.count(User.user_id)).filter(
                User.is_active == True
            ).scalar()
            
            # Admin users
            counts['admin'] = self.db.query(func.count(User.user_id)).filter(
                User.is_admin == True
            ).scalar()
            
            # Users by status
            status_counts = self.db.query(
                User.status, 
                func.count(User.user_id).label('count')
            ).group_by(User.status).all()
            
            counts['by_status'] = {status: count for status, count in status_counts}
            
            logger.debug(f"User counts: {counts}")
            return counts
            
        except Exception as e:
            logger.error(f"Error getting user counts: {str(e)}")
            raise