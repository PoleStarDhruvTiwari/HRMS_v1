import logging
from sqlalchemy import Column, BigInteger, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class EmployeeHierarchy(Base):
    """Employee Hierarchy model representing reporting relationships."""
    
    __tablename__ = "employee_hierarchy"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, index=True)
    reporting_to_id = Column(BigInteger, ForeignKey('users.user_id'), index=True)
    depth = Column(Integer, nullable=False, default=0)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship(
        "ExistingUser", 
        foreign_keys=[user_id],
        backref="hierarchy_entries"
    )
    reporting_to = relationship(
        "ExistingUser", 
        foreign_keys=[reporting_to_id],
        backref="subordinates"
    )
    updater = relationship(
        "ExistingUser", 
        foreign_keys=[updated_by]
    )
    
    def __repr__(self):
        return f"<EmployeeHierarchy(id={self.id}, user_id={self.user_id}, reporting_to={self.reporting_to_id}, depth={self.depth})>"