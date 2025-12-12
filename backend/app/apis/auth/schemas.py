from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
from datetime import datetime


# Request schemas
class GoogleTokenRequest(BaseModel):
    """Request schema for Google OAuth token."""
    token: str


# Response schemas
class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    """Response schema for user data."""
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[HttpUrl] = None
    is_admin: bool = False
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Response schema for login."""
    user: UserResponse
    tokens: TokenResponse


class LogoutResponse(BaseModel):
    """Response schema for logout."""
    message: str = "Logged out successfully"


class RefreshTokenResponse(BaseModel):
    """Response schema for token refresh."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Internal schemas
class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: str
    exp: datetime
    type: str