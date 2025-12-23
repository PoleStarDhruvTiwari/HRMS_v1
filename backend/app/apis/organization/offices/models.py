# app/apis/organization/offices/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class Office(Base):
    """Office model."""
    
    __tablename__ = "offices"
    
    office_id = Column(BigInteger, primary_key=True, index=True)
    office_name = Column(String(150), unique=True, nullable=False, index=True)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    updater = relationship("ExistingUser", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Office(office_id={self.office_id}, name={self.office_name})>"