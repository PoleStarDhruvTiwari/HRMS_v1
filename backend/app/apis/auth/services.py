# app/auth/services.py
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Response, Request

from app.core.security import security_service
from app.core.constants import REFRESH_TOKEN_COOKIE_NAME
from app.core.config import settings
from .repositories import UserRepository, SessionRepository
from .schemas import LoginResponse, UserResponse, TokenResponse


logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository):
        self.user_repo = user_repo
        self.session_repo = session_repo
    
    def google_login(self, google_token: str, response: Response, 
                    device_id: Optional[str] = None, 
                    device_type: Optional[str] = None) -> LoginResponse:
        """Handle Google OAuth login."""
        logger.info("Processing Google login")
        
        try:
            # Verify Google token
            idinfo = security_service.verify_google_token(google_token)
            email = idinfo.get("email")
            name = idinfo.get("name")
            picture = idinfo.get("picture")
            
            if not email:
                logger.error("No email found in Google token")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not found in Google token"
                )
            
            logger.info(f"Google authentication successful for: {email}")
            
            # Check if user exists in the existing users table
            user = self.user_repo.get_by_email(email)
            if not user:
                logger.warning(f"User not found in users table: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authorized. Please contact administrator."
                )
            
            # Check if user is active (case-insensitive check)
            if not user.status or str(user.status).lower() != "active":
                logger.warning(f"Inactive user attempted login: {email} (status: {user.status})")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User account is not active (status: {user.status})"
                )
            
            # Update last login
            self.user_repo.update_last_login(email)
            
            # Create tokens with user_id in payload
            access_token, expires_in = security_service.create_access_token(
                subject=email,  # Fixed: changed 'email' to 'subject'
                user_id=user.user_id
            )
            refresh_token = security_service.create_refresh_token(
                subject=email,  # Fixed: changed 'email' to 'subject'
                user_id=user.user_id
            )
            
            # Calculate refresh token expiration
            refresh_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_EXPIRE_DAYS)
            
            # Create session in database
            session = self.session_repo.create_session(
                user_id=user.user_id,
                refresh_token=refresh_token,
                expires_at=refresh_expires_at,
                device_id=device_id,
                device_type=device_type
            )
            
            # Set refresh token cookie
            self._set_refresh_token_cookie(response, refresh_token)
            
            # Prepare user response
            user_response = UserResponse(
                user_id=user.user_id,
                email=user.email,
                full_name=user.full_name,
                global_employee_id=user.global_employee_id,
                phone_number=user.phone_number,
                location_id=user.location_id,
                team_id=user.team_id,
                vertical_id=user.vertical_id,
                designation_id=user.designation_id,
                status=user.status,
                role_id=user.role_id,
                # Remove is_admin if it doesn't exist in your database
                # is_admin=user.is_admin if hasattr(user, 'is_admin') else False,
                last_login=user.last_login
            )
            
            # Prepare token response
            token_response = TokenResponse(
                access_token=access_token,
                expires_in=expires_in
            )
            
            logger.info(f"Login successful for user: {email} (user_id: {user.user_id}, session_id: {session.session_id})")
            return LoginResponse(user=user_response, tokens=token_response)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during Google login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during authentication"
            )
    
    def refresh_access_token(self, request: Request, response: Response) -> TokenResponse:
        """Refresh access token using refresh token."""
        logger.info("Processing token refresh")
        
        try:
            # Get refresh token from cookie
            refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
            if not refresh_token:
                logger.warning("No refresh token found in cookies")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No refresh token provided"
                )
            
            # Verify refresh token
            payload = security_service.verify_local_token(refresh_token, require_user_id=True)
            if payload.get("type") != "refresh":
                logger.warning("Token is not a refresh token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            email = payload.get("sub")
            user_id = payload.get("user_id")
            
            if not user_id:
                logger.warning("No user_id found in token payload")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Verify token against database session
            session = self.session_repo.get_session_by_refresh_token(refresh_token)
            if not session:
                logger.warning(f"Invalid or expired session for refresh token")
                # Clear invalid cookie
                self._clear_refresh_token_cookie(response)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session"
                )
            
            # Get user to verify
            user = self.user_repo.get_by_user_id(user_id)
            if not user or user.email != email:
                logger.warning(f"User mismatch for session")
                self._clear_refresh_token_cookie(response)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user session"
                )
            
            # Check if user is active (case-insensitive check)
            if not user.status or str(user.status).lower() != "active":
                logger.warning(f"Inactive user attempted token refresh: {email}")
                self._clear_refresh_token_cookie(response)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            # Refresh token rotation: create new refresh token
            new_refresh_token = security_service.create_refresh_token(
                subject=email,  # Fixed: changed 'email' to 'subject'
                user_id=user.user_id
            )
            new_refresh_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_EXPIRE_DAYS)
            
            # Update session with new token
            self.session_repo.update_session_refresh_token(
                session_id=session.session_id,
                new_refresh_token=new_refresh_token,
                new_expires_at=new_refresh_expires_at
            )
            
            # Set new refresh token cookie
            self._set_refresh_token_cookie(response, new_refresh_token)
            
            # Create new access token
            access_token, expires_in = security_service.create_access_token(
                subject=email,  # Fixed: changed 'email' to 'subject'
                user_id=user.user_id
            )
            
            logger.info(f"Token refreshed successfully for user: {email}")
            return TokenResponse(
                access_token=access_token,
                expires_in=expires_in
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during token refresh: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during token refresh"
            )
    
    def get_current_user(self, request: Request) -> UserResponse:
        """Get current authenticated user from access token."""
        logger.debug("Getting current user")
        
        try:
            # Extract and verify access token
            auth_header = request.headers.get("Authorization")
            access_token = security_service.extract_token_from_header(auth_header)
            
            payload = security_service.verify_local_token(access_token, require_user_id=True)
            if payload.get("type") != "access":
                logger.warning("Token is not an access token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            email = payload.get("sub")
            user_id = payload.get("user_id")
            
            # Get user from database
            user = self.user_repo.get_by_email(email)
            if not user:
                logger.warning(f"User not found in database: {email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if user.user_id != user_id:
                logger.warning(f"User ID mismatch: {user.user_id} != {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user credentials"
                )
            
            # Check if user is active (case-insensitive check)
            if not user.status or str(user.status).lower() != "active":
                logger.warning(f"Inactive user attempted access: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            logger.debug(f"Current user retrieved: {email}")
            
            return UserResponse(
                user_id=user.user_id,
                email=user.email,
                full_name=user.full_name,
                global_employee_id=user.global_employee_id,
                phone_number=user.phone_number,
                location_id=user.location_id,
                team_id=user.team_id,
                vertical_id=user.vertical_id,
                designation_id=user.designation_id,
                status=user.status,
                role_id=user.role_id,
                # Remove is_admin if it doesn't exist in your database
                # is_admin=user.is_admin if hasattr(user, 'is_admin') else False,
                last_login=user.last_login
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting current user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def logout(self, request: Request, response: Response) -> Dict[str, str]:
        """Handle user logout."""
        logger.info("Processing logout")
        
        try:
            # Get refresh token from cookie
            refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
            logger.info(refresh_token)
            
            if refresh_token:
                # Delete session by refresh token
                self.session_repo.delete_session_by_refresh_token(refresh_token)
                logger.info("Session deleted for logout")
            
            # Clear refresh token cookie
            self._clear_refresh_token_cookie(response)
            
            logger.info("Logout completed")
            return {"message": "Logged out successfully"}
            
        except Exception as e:
            logger.exception(f"Unexpected error during logout: {str(e)}")
            # Still try to clear the cookie
            self._clear_refresh_token_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during logout"
            )
    
    def logout_all(self, request: Request, response: Response) -> Dict[str, str]:
        """Logout from all devices/sessions."""
        logger.info("Processing logout from all devices")
        
        try:
            # Get refresh token from cookie
            refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
            
            if refresh_token:
                # Verify token to get user info
                try:
                    payload = security_service.verify_local_token(refresh_token)
                    user_id = payload.get("user_id")
                    
                    if user_id:
                        # Delete all sessions for this user
                        deleted_count = self.session_repo.delete_all_user_sessions(user_id)
                        logger.info(f"Deleted {deleted_count} sessions for user_id: {user_id}")
                except HTTPException:
                    # Token is invalid but we still clear the cookie
                    logger.warning("Invalid token during logout_all")
            
            # Clear refresh token cookie
            self._clear_refresh_token_cookie(response)
            
            logger.info("Logout from all devices completed")
            return {"message": "Logged out from all devices successfully"}
            
        except Exception as e:
            logger.exception(f"Unexpected error during logout_all: {str(e)}")
            self._clear_refresh_token_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during logout"
            )
    
    def get_user_sessions(self, request: Request) -> Dict[str, Any]:
        """Get all active sessions for current user."""
        logger.debug("Getting user sessions")
        
        try:
            # Get current user
            auth_header = request.headers.get("Authorization")
            access_token = security_service.extract_token_from_header(auth_header)
            payload = security_service.verify_local_token(access_token, require_user_id=True)
            email = payload.get("sub")
            user_id = payload.get("user_id")
            
            user = self.user_repo.get_by_user_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get all active sessions
            sessions = self.session_repo.get_user_sessions(user.user_id)
            
            return {
                "user_id": user.user_id,
                "email": user.email,
                "active_sessions": len(sessions),
                "sessions": [
                    {
                        "session_id": session.session_id,
                        "device_id": session.device_id,
                        "device_type": session.device_type,
                        "last_login": session.last_login,
                        "created_at": session.created_at
                    }
                    for session in sessions
                ]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting user sessions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _set_refresh_token_cookie(self, response: Response, token: str):
        """Set refresh token as HTTP-only cookie."""
        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=token,
            httponly=True,
            max_age=60 * 60 * 24 * settings.REFRESH_EXPIRE_DAYS,
            samesite=settings.SAME_SITE_COOKIE,
            secure=settings.SECURE_COOKIES,
            path="/api/auth/refresh"
        )
        logger.debug("Refresh token cookie set")
    
    def _clear_refresh_token_cookie(self, response: Response):
        """Clear refresh token cookie."""
        response.delete_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            path="/api/auth/refresh",
            httponly=True,
            samesite=settings.SAME_SITE_COOKIE,
            secure=settings.SECURE_COOKIES
        )
        logger.debug("Refresh token cookie cleared")