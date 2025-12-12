import logging
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.database.session import SessionLocal  # ✅ Import SessionLocal, not get_db
from .repositories import UserRepository
from .services import AuthService
from .schemas import (
    GoogleTokenRequest,
    LoginResponse,
    TokenResponse,
    UserResponse,
    LogoutResponse
)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# FIXED: Dependency injection
def get_db() -> Session:
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


@router.post("/google-login", response_model=LoginResponse)
async def google_login(
    request: GoogleTokenRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user with Google OAuth.
    
    - **token**: Google ID token from frontend
    - Returns: User info and access token
    - Sets: HTTP-only refresh token cookie
    """
    logger.info("Google login endpoint called")
    return auth_service.google_login(request.token, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token from cookie.
    
    - Requires: Refresh token in HTTP-only cookie
    - Returns: New access token
    - Rotates: Refresh token (security best practice)
    """
    logger.info("Token refresh endpoint called")
    return auth_service.refresh_access_token(request, response)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user by clearing refresh token.
    
    - Clears: Refresh token from database and cookie
    - Returns: Success message
    """
    logger.info("Logout endpoint called")
    return auth_service.logout(request, response)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current authenticated user's information.
    
    - Requires: Bearer token in Authorization header
    - Returns: User profile information
    """
    logger.info("Get current user endpoint called")
    return auth_service.get_current_user(request)