# app/auth/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Text, ForeignKey, Date, JSON
from sqlalchemy.sql import func
from app.database.base import Base
from sqlalchemy.orm import relationship
# In app/apis/auth/models.py
# Add this import at the top
from app.apis.access_control.user_permissions.models import UserPermission


logger = logging.getLogger(__name__)


class ExistingUser(Base):
    """Existing user model (mapping to your users table)."""
    
    __tablename__ = "users"
    
    user_id = Column(BigInteger, primary_key=True, index=True)
    global_employee_id = Column(String(20))
    location_id = Column(BigInteger)
    full_name = Column(String(150))
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    team_id = Column(BigInteger)
    vertical_id = Column(BigInteger)
    designation_id = Column(BigInteger)
    date_of_joining = Column(Date)
    date_of_leaving = Column(Date, nullable=True)
    status = Column(String(20), default="active")
    reporting_level1_id = Column(BigInteger, nullable=True)
    reporting_level2_id = Column(BigInteger, nullable=True)
    skills = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    resume = Column(Text, nullable=True)  # Changed from bytea to Text for compatibility
    experience_months = Column(Integer, default=0)
    updated_by = Column(BigInteger)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    role_id = Column(BigInteger)
    
    # Additional fields for authentication
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # ===========================================
    # RELATIONSHIPS
    # ===========================================
    
    # Relationship to user_permissions table
    direct_permissions = relationship(
        "UserPermission", 
        foreign_keys="[UserPermission.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<ExistingUser(user_id={self.user_id}, email={self.email})>"
    


class UserSession(Base):
    """User session model for storing refresh tokens and device info."""
    
    __tablename__ = "user_sessions"
    
    session_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    device_id = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __repr__(self):
        return f"<UserSession(session_id={self.session_id}, user_id={self.user_id})>"