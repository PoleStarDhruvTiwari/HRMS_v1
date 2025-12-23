# app/apis/attendance/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Date, JSON, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
import enum

logger = logging.getLogger(__name__)


# Enums for database
class DayTypeEnum(str, enum.Enum):
    WORKDAY = "workday"
    WEEKOFF = "weekoff"
    HOLIDAY = "holiday"
    COMP_OFF = "comp-off holiday"


class HalfStatusEnum(str, enum.Enum):
    PRESENT = "present"
    LEAVE = "leave"
    ABSENT = "absent"


class LeaveStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EmployeeAvailability(Base):
    """Employee attendance/availability model."""
    
    __tablename__ = "employee_availability"
    
    attendance_id = Column(BigInteger, primary_key=True, index=True)
    #syntax: Column(DataType, ForeignKey('referenced_table(postgres table name).referenced_column'))
    employee_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False, index=True)
    day_type = Column(SQLEnum(DayTypeEnum, values_callable=lambda enum: [e.value for e in enum],native_enum=True ), nullable=False, default=DayTypeEnum.WORKDAY.value)
    first_half = Column(SQLEnum(HalfStatusEnum, values_callable=lambda enum: [e.value for e in enum],native_enum=True ), nullable=False, default=HalfStatusEnum.PRESENT.value)
    second_half = Column(SQLEnum(HalfStatusEnum, values_callable=lambda enum: [e.value for e in enum],native_enum=True ), nullable=False, default=HalfStatusEnum.PRESENT.value)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_in_location_id = Column(BigInteger, ForeignKey('offices.office_id'), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    check_out_location_id = Column(BigInteger, ForeignKey('offices.office_id'), nullable=True)
    total_workhours = Column(Numeric(5, 2), nullable=True)
    shift_id = Column(BigInteger, ForeignKey('shifts.shift_id'), nullable=False)
    leave_applied_by_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    leave_applied_at = Column(DateTime(timezone=True), nullable=True)
    leave_status = Column(SQLEnum(LeaveStatusEnum, values_callable=lambda enum: [e.value for e in enum],native_enum=True ), nullable=True, default=LeaveStatusEnum.PENDING)
    leave_approved_by_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    leave_approved_at = Column(DateTime(timezone=True), nullable=True)
    comment_json = Column(JSON, nullable=True, default={})
    updated_by_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    # syntax: relationship("ModelName", foreign_keys=[foreign_key_column])
    employee = relationship("ExistingUser", foreign_keys=[employee_id])
    check_in_location = relationship("Office", foreign_keys=[check_in_location_id])
    check_out_location = relationship("Office", foreign_keys=[check_out_location_id])
    shift = relationship("Shift")
    leave_applied_by = relationship("ExistingUser", foreign_keys=[leave_applied_by_id])
    leave_approved_by = relationship("ExistingUser", foreign_keys=[leave_approved_by_id])
    updated_by = relationship("ExistingUser", foreign_keys=[updated_by_id])
    
    def __repr__(self):
        return f"<EmployeeAvailability(attendance_id={self.attendance_id}, employee_id={self.employee_id}, date={self.attendance_date})>"


# Optional: If you have these tables, create models for them


# class Office(Base):
#     """Office/location model."""
#     __tablename__ = "offices"
    
#     office_id = Column(BigInteger, primary_key=True, index=True)
#     office_name = Column(String(100), nullable=False)
#     address = Column(String(500), nullable=True)
#     city = Column(String(100), nullable=True)
#     state = Column(String(100), nullable=True)
#     country = Column(String(100), nullable=True)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# class Shift(Base):
#     """Shift model."""
#     __tablename__ = "shifts"
    
#     shift_id = Column(BigInteger, primary_key=True, index=True)
#     shift_name = Column(String(100), nullable=False)
#     start_time = Column(DateTime(timezone=True), nullable=False)
#     end_time = Column(DateTime(timezone=True), nullable=False)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())