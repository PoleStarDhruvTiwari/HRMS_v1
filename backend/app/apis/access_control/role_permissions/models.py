# app/apis/access_control/role_permissions/models.py
"""
Role-Permission Models
"""

import logging
from sqlalchemy import Column, DateTime, BigInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from app.database.base import Base

logger = logging.getLogger(__name__)


class RolePermission(Base):
    """Role-Permission assignment model."""
    
    __tablename__ = "role_permissions"
    
    role_permission_id = Column(BigInteger, primary_key=True, index=True)
    role_id = Column(BigInteger, ForeignKey('roles.role_id', ondelete='CASCADE'), nullable=False, index=True)
    permission_id = Column(BigInteger, ForeignKey('permissions.permission_id', ondelete='CASCADE'), nullable=False, index=True)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    role = relationship("Role", foreign_keys=[role_id])
    permission = relationship("Permission", foreign_keys=[permission_id])
    updater = relationship("ExistingUser", foreign_keys=[updated_by])
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )
    
    def __repr__(self):
        return f"<RolePermission(role={self.role_id}, permission={self.permission_id})>"