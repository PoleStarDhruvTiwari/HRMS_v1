# app/auth/repositories.py
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import ExistingUser, UserSession


logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for ExistingUser database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_email(self, email: str) -> Optional[ExistingUser]:
        """Get user by email."""
        logger.debug(f"Fetching user by email: {email}")
        try:
            user = self.db.query(ExistingUser).filter(ExistingUser.email == email).first()
            if user:
                logger.debug(f"User found: {user.email}")
            else:
                logger.debug(f"No user found with email: {email}")
            return user
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {str(e)}")
            raise
    
    def get_by_user_id(self, user_id: int) -> Optional[ExistingUser]:
        """Get user by user_id."""
        logger.debug(f"Fetching user by user_id: {user_id}")
        try:
            user = self.db.query(ExistingUser).filter(ExistingUser.user_id == user_id).first()
            return user
        except Exception as e:
            logger.error(f"Error fetching user by user_id {user_id}: {str(e)}")
            raise
    
    def verify_user_exists(self, email: str) -> bool:
        """Check if user exists in the database."""
        logger.debug(f"Verifying user exists: {email}")
        try:
            user = self.db.query(ExistingUser).filter(ExistingUser.email == email).first()
            exists = user is not None
            if exists:
                logger.debug(f"User exists: {email}")
            else:
                logger.warning(f"User does not exist: {email}")
            return exists
        except Exception as e:
            logger.error(f"Error verifying user {email}: {str(e)}")
            raise
    
    def update_user(self, user: ExistingUser, **kwargs) -> ExistingUser:
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
    
    def update_last_login(self, email: str) -> Optional[ExistingUser]:
        """Update user's last login timestamp."""
        logger.debug(f"Updating last login for user: {email}")
        
        user = self.get_by_email(email)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            logger.debug(f"Last login updated for user: {email}")
        else:
            logger.warning(f"User not found for last login update: {email}")
        
        return user


class SessionRepository:
    """Repository for UserSession database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, user_id: int, refresh_token: str, expires_at: datetime,
                      device_id: Optional[str] = None, device_type: Optional[str] = None) -> UserSession:
        """Create a new user session."""
        logger.info(f"Creating new session for user_id: {user_id}")
        
        try:
            session = UserSession(
                user_id=user_id,
                device_id=device_id,
                device_type=device_type,
                refresh_token=refresh_token,
                expires_at=expires_at,
                last_login=datetime.utcnow()
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Session created successfully: {session.session_id}")
            return session
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating session for user {user_id}: {str(e)}")
            raise
    
    def get_session_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """Get session by refresh token."""
        logger.debug("Fetching session by refresh token")
        try:
            # Check if token is still valid (not expired)
            current_time = datetime.utcnow()
            session = self.db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.expires_at > current_time
            ).first()
            
            if session:
                logger.debug(f"Session found by refresh token: {session.session_id}")
            else:
                logger.debug("No valid session found with provided refresh token")
            
            return session
        except Exception as e:
            logger.error(f"Error fetching session by refresh token: {str(e)}")
            raise
    
    def get_user_sessions(self, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user."""
        logger.debug(f"Fetching sessions for user_id: {user_id}")
        try:
            current_time = datetime.utcnow()
            sessions = self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.expires_at > current_time
            ).order_by(desc(UserSession.created_at)).all()
            
            logger.debug(f"Found {len(sessions)} active sessions for user {user_id}")
            return sessions
        except Exception as e:
            logger.error(f"Error fetching sessions for user {user_id}: {str(e)}")
            raise
    
    def update_session_refresh_token(self, session_id: int, new_refresh_token: str, 
                                   new_expires_at: datetime) -> Optional[UserSession]:
        """Update refresh token for an existing session (token rotation)."""
        logger.debug(f"Updating refresh token for session: {session_id}")
        
        try:
            session = self.db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if session:
                session.refresh_token = new_refresh_token
                session.expires_at = new_expires_at
                session.last_login = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(session)
                logger.debug(f"Session updated successfully: {session_id}")
            else:
                logger.warning(f"Session not found: {session_id}")
            
            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating session {session_id}: {str(e)}")
            raise
    
    def delete_session(self, session_id: int) -> bool:
        """Delete a specific session."""
        logger.debug(f"Deleting session: {session_id}")
        
        try:
            session = self.db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if session:
                self.db.delete(session)
                self.db.commit()
                logger.debug(f"Session deleted successfully: {session_id}")
                return True
            else:
                logger.warning(f"Session not found for deletion: {session_id}")
                return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            raise
    
    def delete_session_by_refresh_token(self, refresh_token: str) -> bool:
        """Delete session by refresh token."""
        logger.debug("Deleting session by refresh token")
        
        try:
            session = self.db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token
            ).first()
            
            if session:
                self.db.delete(session)
                self.db.commit()
                logger.debug(f"Session deleted by refresh token: {session.session_id}")
                return True
            else:
                logger.debug("No session found with provided refresh token")
                return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting session by refresh token: {str(e)}")
            raise
    
    def delete_all_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user (logout from all devices)."""
        logger.debug(f"Deleting all sessions for user_id: {user_id}")
        
        try:
            result = self.db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).delete()
            
            self.db.commit()
            logger.debug(f"Deleted {result} sessions for user {user_id}")
            return result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting sessions for user {user_id}: {str(e)}")
            raise
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        logger.debug("Cleaning up expired sessions")
        
        try:
            current_time = datetime.utcnow()
            result = self.db.query(UserSession).filter(
                UserSession.expires_at <= current_time
            ).delete()
            
            self.db.commit()
            logger.debug(f"Cleaned up {result} expired sessions")
            return result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            raise