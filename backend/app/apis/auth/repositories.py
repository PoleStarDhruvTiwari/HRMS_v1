import logging
from typing import Optional
from sqlalchemy.orm import Session

from .models import User


logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        logger.debug(f"Fetching user by email: {email}")
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if user:
                logger.debug(f"User found: {user.email}")
            else:
                logger.debug(f"No user found with email: {email}")
            return user
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {str(e)}")
            raise
    
    def get_by_refresh_token(self, refresh_token: str) -> Optional[User]:
        """Get user by refresh token."""
        logger.debug(f"Fetching user by refresh token")
        try:
            user = self.db.query(User).filter(
                User.refresh_token == refresh_token,
                User.is_active == True
            ).first()
            
            if user:
                logger.debug(f"User found by refresh token: {user.email}")
            else:
                logger.debug("No user found with provided refresh token")
            
            return user
        except Exception as e:
            logger.error(f"Error fetching user by refresh token: {str(e)}")
            raise
    
    def create_user(self, email: str, name: Optional[str] = None,
                   picture: Optional[str] = None) -> User:
        """Create a new user."""
        logger.info(f"Creating new user: {email}")
        
        try:
            user = User(
                email=email,
                name=name,
                picture=picture
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User created successfully: {user.email}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user {email}: {str(e)}")
            raise
    
    def update_user(self, user: User, **kwargs) -> User:
        """Update user information."""
        logger.debug(f"Updating user: {user.email}")
        
        try:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
                    logger.debug(f"Updated {key} for user {user.email}")
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.debug(f"User updated successfully: {user.email}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user.email}: {str(e)}")
            raise
    
    def update_refresh_token(self, email: str, refresh_token: str) -> Optional[User]:
        """Update user's refresh token."""
        logger.debug(f"Updating refresh token for user: {email}")
        
        user = self.get_by_email(email)
        if user:
            user.refresh_token = refresh_token
            self.db.commit()
            self.db.refresh(user)
            logger.debug(f"Refresh token updated for user: {email}")
        else:
            logger.warning(f"User not found for refresh token update: {email}")
        
        return user
    
    def clear_refresh_token(self, email: str) -> bool:
        """Clear user's refresh token (logout)."""
        logger.debug(f"Clearing refresh token for user: {email}")
        
        user = self.get_by_email(email)
        if user:
            user.refresh_token = None
            self.db.commit()
            logger.debug(f"Refresh token cleared for user: {email}")
            return True
        
        logger.warning(f"User not found for token clearance: {email}")
        return False