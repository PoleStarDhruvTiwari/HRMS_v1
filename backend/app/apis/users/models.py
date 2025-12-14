# app/apis/users/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Date, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class User(Base):
    """User model for API operations."""
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
    reporting_level1_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    reporting_level2_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    skills = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    resume = Column(Text, nullable=True)  # Changed from bytea to Text for easier handling
    experience_months = Column(Integer, default=0)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    role_id = Column(BigInteger)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    reporting_level1 = relationship("User", foreign_keys=[reporting_level1_id], remote_side=[user_id])
    reporting_level2 = relationship("User", foreign_keys=[reporting_level2_id], remote_side=[user_id])
    updater = relationship("User", foreign_keys=[updated_by], remote_side=[user_id])
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"