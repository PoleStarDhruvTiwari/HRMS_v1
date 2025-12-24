
# app/apis/access_control/user_permissions/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Date, JSON, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from app.database.base import Base
import enum

logger = logging.getLogger(__name__)


# Define ENUM for permission status
class UserPermissionStatus(str, enum.Enum):
    GRANTED = "granted"     # Extra permission added
    REVOKED = "revoked"     # Permission revoked from role
    ACTIVE = "active"       # Active permission (legacy support)
    INACTIVE = "inactive"   # Inactive permission (legacy support)


class UserPermission(Base):
    """Direct permission assignment or revocation for users."""
    
    __tablename__ = "user_permissions"
    
    user_permission_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    permission_id = Column(BigInteger, ForeignKey('permissions.permission_id', ondelete='CASCADE'), nullable=False, index=True)
    #day_type = Column(SQLEnum(DayTypeEnum, values_callable=lambda enum: [e.value for e in enum],native_enum=True ), nullable=False, default=DayTypeEnum.WORKDAY.value)
    # This is example whenever use enum follow this format 
    #status = Column(Enum(UserPermissionStatus), nullable=False, default=UserPermissionStatus.GRANTED)
    status = Column(SQLEnum(UserPermissionStatus, values_callable=lambda enum: [e.value for e in enum], native_enum=True), nullable=False, default=UserPermissionStatus.GRANTED.value)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("ExistingUser", foreign_keys=[user_id], back_populates="direct_permissions")
    permission = relationship("Permission", foreign_keys=[permission_id])
    updater = relationship("ExistingUser", foreign_keys=[updated_by])
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_id', name='uq_user_permission'),
    )
    
    def __repr__(self):
        return f"<UserPermission(user={self.user_id}, permission={self.permission_id}, status={self.status})>"
    
    @property
    def is_granted(self) -> bool:
        """Check if permission is granted (extra permission)."""
        return self.status == UserPermissionStatus.GRANTED
    
    @property
    def is_revoked(self) -> bool:
        """Check if permission is revoked (removed from role)."""
        return self.status == UserPermissionStatus.REVOKED