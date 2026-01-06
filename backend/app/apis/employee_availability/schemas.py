# # app/apis/attendance/schemas.py
# from pydantic import BaseModel, Field, validator, ConfigDict
# from typing import Optional, List, Dict, Any
# from datetime import datetime, date, time
# from enum import Enum


# # Enums for Pydantic
# class DayType(str, Enum):
#     WORKDAY = "workday"
#     WEEKOFF = "weekoff"
#     HOLIDAY = "holiday"
#     COMP_OFF = "comp-off holiday"


# class HalfStatus(str, Enum):
#     PRESENT = "present"
#     LEAVE = "leave"
#     ABSENT = "absent"


# class LeaveStatus(str, Enum):
#     PENDING = "pending"
#     APPROVED = "approved"
#     REJECTED = "rejected"


# # Base schemas
# class EmployeeAvailabilityBase(BaseModel):
#     employee_id: int
#     attendance_date: date
#     day_type: DayType = DayType.WORKDAY
#     first_half: HalfStatus = HalfStatus.PRESENT
#     second_half: HalfStatus = HalfStatus.PRESENT
#     check_in_time: Optional[datetime] = None
#     check_in_location_id: Optional[int] = None
#     check_out_time: Optional[datetime] = None
#     check_out_location_id: Optional[int] = None
#     total_workhours: Optional[float] = Field(None, ge=0, le=24)
#     shift_id: int
#     comment_json: Optional[Dict[str, Any]] = {}
    
#     @validator('attendance_date')
#     def validate_date_not_future(cls, v):
#         if v > date.today():
#             raise ValueError('Attendance date cannot be in the future')
#         return v
    
#     @validator('total_workhours')
#     def validate_workhours(cls, v):
#         if v is not None and (v < 0 or v > 24):
#             raise ValueError('Work hours must be between 0 and 24')
#         return v


# class EmployeeAvailabilityCreate(EmployeeAvailabilityBase):
#     pass


# class EmployeeAvailabilityUpdate(BaseModel):
#     day_type: Optional[DayType] = None
#     first_half: Optional[HalfStatus] = None
#     second_half: Optional[HalfStatus] = None
#     check_in_time: Optional[datetime] = None
#     check_in_location_id: Optional[int] = None
#     check_out_time: Optional[datetime] = None
#     check_out_location_id: Optional[int] = None
#     total_workhours: Optional[float] = Field(None, ge=0, le=24)
#     shift_id: Optional[int] = None
#     comment_json: Optional[Dict[str, Any]] = None


# # Leave related schemas
# class LeaveApplyRequest(BaseModel):
#     employee_id: int
#     attendance_date: date
#     half_type: str = Field(..., pattern="^(first|second|full)$")
#     reason: Optional[str] = None
#     comment_json: Optional[Dict[str, Any]] = {}


# class LeaveActionRequest(BaseModel):
#     attendance_id: int
#     action: LeaveStatus = LeaveStatus.APPROVED
#     comments: Optional[str] = None


# class CheckInRequest(BaseModel):
#     employee_id: int
#     check_in_location_id: int
#     check_in_time: Optional[datetime] = None
#     comment_json: Optional[Dict[str, Any]] = {}


# class CheckOutRequest(BaseModel):
#     employee_id: int
#     check_out_location_id: int
#     check_out_time: Optional[datetime] = None
#     comment_json: Optional[Dict[str, Any]] = {}


# # Response schemas
# class EmployeeAvailabilityResponse(EmployeeAvailabilityBase):
#     attendance_id: int
#     leave_applied_by_id: Optional[int] = None
#     leave_applied_at: Optional[datetime] = None
#     leave_status: Optional[LeaveStatus] = None
#     leave_approved_by_id: Optional[int] = None
#     leave_approved_at: Optional[datetime] = None
#     updated_by_id: int
#     updated_at: Optional[datetime] = None
#     created_at: Optional[datetime] = None
    
#     # Related data
#     employee_name: Optional[str] = None
#     shift_name: Optional[str] = None
#     check_in_location_name: Optional[str] = None
#     check_out_location_name: Optional[str] = None
    
#     model_config = ConfigDict(from_attributes=True)


# class AttendanceSummaryResponse(BaseModel):
#     employee_id: int
#     employee_name: str
#     month: int
#     year: int
#     total_days: int
#     present_days: int
#     leave_days: int
#     absent_days: int
#     weekoff_days: int
#     holiday_days: int
#     total_work_hours: float
#     avg_daily_hours: float


# class AttendanceListResponse(BaseModel):
#     attendances: List[EmployeeAvailabilityResponse]
#     total: int
#     page: int
#     page_size: int
#     total_pages: int


# # Filter schemas
# class AttendanceFilter(BaseModel):
#     employee_id: Optional[int] = None
#     start_date: Optional[date] = None
#     end_date: Optional[date] = None
#     month: Optional[int] = Field(None, ge=1, le=12)
#     year: Optional[int] = None
#     day_type: Optional[DayType] = None
#     first_half: Optional[HalfStatus] = None
#     second_half: Optional[HalfStatus] = None
#     leave_status: Optional[LeaveStatus] = None
#     shift_id: Optional[int] = None
    
#     @validator('end_date', always=True)
#     def validate_date_range(cls, v, values):
#         if 'start_date' in values and values['start_date'] and v:
#             if v < values['start_date']:
#                 raise ValueError('End date must be after start date')
#         return v


# # Statistics schemas
# class AttendanceStatsResponse(BaseModel):
#     employee_id: int
#     date_range: str
#     present_count: int
#     leave_count: int
#     absent_count: int
#     total_work_hours: float
#     on_time_arrivals: int
#     late_arrivals: int
#     early_departures: int
#     average_hours_per_day: float 



# app/apis/attendance/schemas.py
from pydantic import BaseModel, Field, validator, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum


# Enums for Pydantic
class DayType(str, Enum):
    WORKDAY = "workday"
    WEEKOFF = "weekoff"
    HOLIDAY = "holiday"
    COMP_OFF = "comp-off holiday"


class HalfStatus(str, Enum):
    NA = "na"  # Added missing value
    PRESENT = "present"
    LEAVE = "leave"
    ABSENT = "absent"


class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# Base schemas
class EmployeeAvailabilityBase(BaseModel):
    employee_id: int
    attendance_date: date
    day_type: DayType = DayType.WORKDAY
    first_half: Optional[HalfStatus] = HalfStatus.NA  # Changed to Optional with NA default
    second_half: Optional[HalfStatus] = HalfStatus.NA  # Changed to Optional with NA default
    check_in_time: Optional[datetime] = None
    check_in_location_id: Optional[int] = None
    check_out_time: Optional[datetime] = None
    check_out_location_id: Optional[int] = None
    total_workhours: Optional[float] = Field(None, ge=0, le=24)
    shift_id: int
    comment_json: Optional[Dict[str, Any]] = {}
    
    @field_validator('attendance_date')
    @classmethod
    def validate_date_not_future(cls, v):
        if v > date.today():
            raise ValueError('Attendance date cannot be in the future')
        return v
    
    @field_validator('total_workhours')
    @classmethod
    def validate_workhours(cls, v):
        if v is not None and (v < 0 or v > 24):
            raise ValueError('Work hours must be between 0 and 24')
        return v


class EmployeeAvailabilityCreate(EmployeeAvailabilityBase):
    """Schema for creating attendance record."""
    updated_by_id: int  # Required for creation


class EmployeeAvailabilityUpdate(BaseModel):
    """Schema for updating attendance record."""
    day_type: Optional[DayType] = None
    first_half: Optional[HalfStatus] = None
    second_half: Optional[HalfStatus] = None
    check_in_time: Optional[datetime] = None
    check_in_location_id: Optional[int] = None
    check_out_time: Optional[datetime] = None
    check_out_location_id: Optional[int] = None
    total_workhours: Optional[float] = Field(None, ge=0, le=24)
    shift_id: Optional[int] = None
    comment_json: Optional[Dict[str, Any]] = None
    leave_status: Optional[LeaveStatus] = None  # Added for leave approval
    updated_by_id: Optional[int] = None  # For updates


# Leave related schemas
class LeaveApplyRequest(BaseModel):
    """Schema for applying for leave."""
    employee_id: int
    attendance_date: date
    half_type: str = Field(..., pattern="^(first|second|full)$")
    reason: Optional[str] = None
    comment_json: Optional[Dict[str, Any]] = {}
    leave_applied_by_id: int  # Who is applying the leave


class LeaveActionRequest(BaseModel):
    """Schema for approving/rejecting leave."""
    attendance_id: int
    action: LeaveStatus = LeaveStatus.APPROVED
    comments: Optional[str] = None
    leave_approved_by_id: int  # Who is approving/rejecting


class CheckInRequest(BaseModel):
    """Schema for check-in."""
    employee_id: int
    check_in_location_id: int
    check_in_time: Optional[datetime] = None
    comment_json: Optional[Dict[str, Any]] = {}
    updated_by_id: int  # Who is performing the check-in


class CheckOutRequest(BaseModel):
    """Schema for check-out."""
    employee_id: int
    check_out_location_id: int
    check_out_time: Optional[datetime] = None
    comment_json: Optional[Dict[str, Any]] = {}
    updated_by_id: int  # Who is performing the check-out


# Response schemas
class EmployeeAvailabilityResponse(EmployeeAvailabilityBase):
    """Full response schema with all fields."""
    attendance_id: int
    leave_applied_by_id: Optional[int] = None
    leave_applied_at: Optional[datetime] = None
    leave_status: Optional[LeaveStatus] = None
    leave_approved_by_id: Optional[int] = None
    leave_approved_at: Optional[datetime] = None
    updated_by_id: int
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    # Related data (can be populated via joins)
    employee_name: Optional[str] = None
    shift_name: Optional[str] = None
    check_in_location_name: Optional[str] = None
    check_out_location_name: Optional[str] = None
    leave_applied_by_name: Optional[str] = None
    leave_approved_by_name: Optional[str] = None
    updated_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AttendanceSummaryResponse(BaseModel):
    """Monthly/period summary response."""
    employee_id: int
    employee_name: str
    month: int
    year: int
    total_days: int
    present_days: int
    leave_days: int
    absent_days: int
    weekoff_days: int
    holiday_days: int
    total_work_hours: float
    avg_daily_hours: float
    # Additional metrics
    half_day_leaves: int = 0
    full_day_leaves: int = 0


class AttendanceListResponse(BaseModel):
    """Paginated list response."""
    attendances: List[EmployeeAvailabilityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Filter schemas
class AttendanceFilter(BaseModel):
    """Filter for querying attendance records."""
    employee_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = None
    day_type: Optional[DayType] = None
    first_half: Optional[HalfStatus] = None
    second_half: Optional[HalfStatus] = None
    leave_status: Optional[LeaveStatus] = None
    shift_id: Optional[int] = None
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        start_date = info.data.get('start_date')
        if start_date and v and v < start_date:
            raise ValueError('End date must be after start date')
        return v


# Statistics schemas
class AttendanceStatsResponse(BaseModel):
    """Detailed statistics response."""
    employee_id: int
    date_range: str
    present_count: int
    leave_count: int
    absent_count: int
    total_work_hours: float
    on_time_arrivals: int
    late_arrivals: int
    early_departures: int
    average_hours_per_day: float
    # Additional stats
    attendance_rate: float  # percentage
    leave_approval_rate: float  # percentage


# Simplified schemas for specific operations
class BulkAttendanceCreate(BaseModel):
    """Schema for bulk attendance creation."""
    records: List[EmployeeAvailabilityCreate]
    updated_by_id: int


class AttendanceBulkUpdate(BaseModel):
    """Schema for bulk attendance updates."""
    attendance_ids: List[int]
    updates: EmployeeAvailabilityUpdate
    updated_by_id: int