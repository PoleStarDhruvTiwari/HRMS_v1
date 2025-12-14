# app/auth/schemas.py
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


# Request schemas
class GoogleTokenRequest(BaseModel):
    """Request schema for Google OAuth token."""
    token: str


class DeviceInfo(BaseModel):
    """Device information for session management."""
    device_id: Optional[str] = None
    device_type: Optional[str] = None


# Response schemas
class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    """Response schema for user data."""
    user_id: int
    email: EmailStr
    full_name: Optional[str] = None
    global_employee_id: Optional[str] = None
    phone_number: Optional[str] = None
    location_id: Optional[int] = None
    team_id: Optional[int] = None
    vertical_id: Optional[int] = None
    designation_id: Optional[int] = None
    status: Optional[str] = None
    role_id: Optional[int] = None
    is_admin: bool = False
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    """Session information."""
    session_id: int
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime


class UserSessionsResponse(BaseModel):
    """Response schema for user sessions."""
    user_id: int
    email: EmailStr
    active_sessions: int
    sessions: List[SessionInfo]


class LoginResponse(BaseModel):
    """Response schema for login."""
    user: UserResponse
    tokens: TokenResponse


class LogoutResponse(BaseModel):
    """Response schema for logout."""
    message: str = "Logged out successfully"


# Internal schemas
class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: str  # email
    user_id: int
    exp: datetime
    type: str