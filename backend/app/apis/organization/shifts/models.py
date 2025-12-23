# app/apis/organization/shifts/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Time, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class Shift(Base):
    """Shift model."""
    
    __tablename__ = "shifts"
    
    shift_id = Column(BigInteger, primary_key=True, index=True)
    shift_name = Column(String(10), unique=True, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    updater = relationship("ExistingUser", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Shift(shift_id={self.shift_id}, name={self.shift_name})>"