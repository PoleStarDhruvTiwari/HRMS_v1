import logging
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base


logger = logging.getLogger(__name__)


class EmployeeProfile(Base):
    """Employee profile model."""
    
    __tablename__ = "employee_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Personal Information
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    nationality = Column(String(100), nullable=True)
    
    # Contact Information
    phone_number = Column(String(20), nullable=True)
    personal_email = Column(String(255), nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_number = Column(String(20), nullable=True)
    
    # Employment Information
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    employment_type = Column(String(50), nullable=True)  # Full-time, Part-time, Contract
    date_of_joining = Column(Date, nullable=True)
    employee_status = Column(String(50), default="Active")  # Active, Inactive, On Leave
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Additional Information
    bio = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)  # JSON or comma-separated
    
    # System fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    user = relationship("User", backref="employee_profile", lazy="joined")
    
    def __repr__(self):
        return f"<EmployeeProfile(id={self.id}, employee_id={self.employee_id})>"


class EmployeeDocument(Base):
    """Employee documents model."""
    
    __tablename__ = "employee_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=False)
    
    document_type = Column(String(100), nullable=False)  # Resume, ID Proof, Contract, etc.
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    employee = relationship("EmployeeProfile", backref="documents")
    
    def __repr__(self):
        return f"<EmployeeDocument(id={self.id}, type={self.document_type})>"