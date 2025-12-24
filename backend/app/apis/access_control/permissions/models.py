# app/apis/access_control/permissions/models.py
"""
Permission Model Definition

IMPORTANT: This model is READ-ONLY from the application perspective.
All changes are managed by the automatic sync system.
"""

import logging
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class Permission(Base):
    """Permission model - READ ONLY for application."""
    
    __tablename__ = "permissions"
    
    permission_id = Column(BigInteger, primary_key=True, index=True)
    permission_key = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(10), nullable=False, default='active')  # 'active' or 'deleted'
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    updater = relationship("ExistingUser", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Permission(id={self.permission_id}, key={self.permission_key}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if permission is active."""
        return self.status == 'active'
    
    @property
    def is_deleted(self) -> bool:
        """Check if permission is soft-deleted."""
        return self.status == 'deleted'