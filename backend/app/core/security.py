import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from fastapi import HTTPException, status

from .config import settings


logger = logging.getLogger(__name__)


class SecurityService:
    """Handles all security-related operations including JWT and OAuth."""
    
    @staticmethod
    def verify_google_token(token: str) -> Dict[str, Any]:
        """Verify Google OAuth token and extract user information."""
        logger.debug(f"Verifying Google token: {token[:20]}...")
        
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                grequests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            
            logger.info(f"Google token verified for: {idinfo.get('email')}")
            return idinfo
            
        except ValueError as e:
            logger.error(f"Invalid Google token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token"
            )
        except Exception as e:
            logger.exception(f"Unexpected error verifying Google token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying authentication token"
            )
    
    @staticmethod
    def create_access_token(subject: str) -> Tuple[str, int]:
        """Create JWT access token."""
        logger.debug(f"Creating access token for subject: {subject}")
        
        try:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_EXPIRE_MINUTES
            )
            payload = {
                "sub": subject,
                "exp": expire,
                "type": "access"
            }
            
            token = jwt.encode(
                payload,
                settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM
            )
            
            expires_in = int((expire - datetime.now(timezone.utc)).total_seconds())
            logger.debug(f"Access token created, expires in {expires_in} seconds")
            
            return token, expires_in
            
        except Exception as e:
            logger.exception(f"Error creating access token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating access token"
            )
    
    @staticmethod
    def create_refresh_token(subject: str) -> str:
        """Create JWT refresh token."""
        logger.debug(f"Creating refresh token for subject: {subject}")
        
        try:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_EXPIRE_DAYS
            )
            payload = {
                "sub": subject,
                "exp": expire,
                "type": "refresh"
            }
            
            token = jwt.encode(
                payload,
                settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM
            )
            
            logger.debug(f"Refresh token created, expires on {expire}")
            return token
            
        except Exception as e:
            logger.exception(f"Error creating refresh token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating refresh token"
            )
    
    @staticmethod
    def verify_local_token(token: str) -> Dict[str, Any]:
        """Verify locally issued JWT token."""
        logger.debug(f"Verifying local token: {token[:20]}...")
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            logger.debug(f"Token verified for subject: {payload.get('sub')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        except Exception as e:
            logger.exception(f"Unexpected error verifying token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying token"
            )
    
    @staticmethod
    def extract_token_from_header(auth_header: Optional[str]) -> str:
        """Extract Bearer token from Authorization header."""
        if not auth_header:
            logger.warning("Missing Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header"
            )
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                logger.warning(f"Invalid scheme in Authorization header: {scheme}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Authorization scheme"
                )
            
            return token
            
        except ValueError:
            logger.warning("Invalid Authorization header format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format"
            )


# Singleton instance
security_service = SecurityService()