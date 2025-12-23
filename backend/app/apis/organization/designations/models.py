# app/apis/organization/designations/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class Designation(Base):
    """Designation model."""
    
    __tablename__ = "designations"
    
    designation_id = Column(BigInteger, primary_key=True, index=True)
    designation_code = Column(String(20), unique=True, nullable=False, index=True)
    designation_name = Column(String(100), unique=True, nullable=False, index=True)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    updater = relationship("ExistingUser", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Designation(designation_id={self.designation_id}, code={self.designation_code}, name={self.designation_name})>"