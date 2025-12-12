import logging
from typing import Optional, Tuple, Dict, Any
from fastapi import HTTPException, status, Response

from app.core.security import security_service
from app.core.constants import REFRESH_TOKEN_COOKIE_NAME
from app.core.config import settings
from .repositories import UserRepository
from .schemas import LoginResponse, UserResponse, TokenResponse


logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def google_login(self, google_token: str, response: Response) -> LoginResponse:
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
            
            # Create or update user
            user = self.user_repo.get_by_email(email)
            if not user:
                logger.info(f"Creating new user: {email}")
                user = self.user_repo.create_user(email, name, picture)
            else:
                logger.info(f"Updating existing user: {email}")
                user = self.user_repo.update_user(user, name=name, picture=picture)
            
            # Create tokens
            access_token, expires_in = security_service.create_access_token(email)
            refresh_token = security_service.create_refresh_token(email)
            
            # Update refresh token in database
            self.user_repo.update_refresh_token(email, refresh_token)
            
            # Set refresh token cookie
            self._set_refresh_token_cookie(response, refresh_token)
            
            # Prepare response
            user_response = UserResponse.from_orm(user)
            token_response = TokenResponse(
                access_token=access_token,
                expires_in=expires_in
            )
            
            logger.info(f"Login successful for user: {email}")
            return LoginResponse(user=user_response, tokens=token_response)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during Google login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during authentication"
            )
    
    def refresh_access_token(self, request, response: Response) -> TokenResponse:
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
            payload = security_service.verify_local_token(refresh_token)
            if payload.get("type") != "refresh":
                logger.warning("Token is not a refresh token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            email = payload.get("sub")
            
            # Verify token against database
            user = self.user_repo.get_by_refresh_token(refresh_token)
            if not user or user.email != email:
                logger.warning(f"Invalid or revoked refresh token for user: {email}")
                # Clear invalid cookie
                self._clear_refresh_token_cookie(response)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked refresh token"
                )
            
            # Refresh token rotation: create new refresh token
            new_refresh_token = security_service.create_refresh_token(email)
            self.user_repo.update_refresh_token(email, new_refresh_token)
            
            # Set new refresh token cookie
            self._set_refresh_token_cookie(response, new_refresh_token)
            
            # Create new access token
            access_token, expires_in = security_service.create_access_token(email)
            
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
    
    def logout(self, request, response: Response) -> Dict[str, str]:
        """Handle user logout."""
        logger.info("Processing logout")
        
        try:
            # Get refresh token from cookie
            refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
            
            if refresh_token:
                # Verify token to get email
                try:
                    payload = security_service.verify_local_token(refresh_token)
                    email = payload.get("sub")
                    
                    # Clear refresh token from database
                    if email:
                        self.user_repo.clear_refresh_token(email)
                        logger.info(f"Logout successful for user: {email}")
                    else:
                        logger.warning("No email found in refresh token during logout")
                except HTTPException:
                    # Token is invalid but we still clear the cookie
                    logger.warning("Invalid token during logout, clearing cookie anyway")
            
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
    
    def get_current_user(self, request) -> UserResponse:
        """Get current authenticated user from access token."""
        logger.debug("Getting current user")
        
        try:
            # Extract and verify access token
            auth_header = request.headers.get("Authorization")
            access_token = security_service.extract_token_from_header(auth_header)
            
            payload = security_service.verify_local_token(access_token)
            if payload.get("type") != "access":
                logger.warning("Token is not an access token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            email = payload.get("sub")
            
            # Get user from database
            user = self.user_repo.get_by_email(email)
            if not user:
                logger.warning(f"User not found in database: {email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if not user.is_active:
                logger.warning(f"Inactive user attempted access: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            logger.debug(f"Current user retrieved: {email}")
            return UserResponse.from_orm(user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting current user: {str(e)}")
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