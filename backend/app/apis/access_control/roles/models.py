# app/apis/roles/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class Role(Base):
    """Role model."""
    
    __tablename__ = "roles"
    
    role_id = Column(BigInteger, primary_key=True, index=True)
    role_code = Column(String(10), unique=True, nullable=False, index=True)
    role_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    updated_by_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    updated_by = relationship("ExistingUser", foreign_keys=[updated_by_id])
    
    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_code={self.role_code})>"