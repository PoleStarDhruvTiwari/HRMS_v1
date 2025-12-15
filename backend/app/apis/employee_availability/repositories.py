# app/apis/attendance/repositories.py
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func, extract, case, cast, String
from sqlalchemy.sql import text

from .models import EmployeeAvailability, DayTypeEnum, HalfStatusEnum, LeaveStatusEnum
from .schemas import AttendanceFilter

logger = logging.getLogger(__name__)


class AttendanceRepository:
    """Repository for EmployeeAvailability database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, attendance_id: int) -> Optional[EmployeeAvailability]:
        """Get attendance record by ID."""
        logger.debug(f"Fetching attendance by ID: {attendance_id}")
        try:
            record = self.db.query(EmployeeAvailability).filter(
                EmployeeAvailability.attendance_id == attendance_id
            ).first()
            return record
        except Exception as e:
            logger.error(f"Error fetching attendance by ID {attendance_id}: {str(e)}")
            raise
    
    def get_by_employee_date(self, employee_id: int, attendance_date: date) -> Optional[EmployeeAvailability]:
        """Get attendance record by employee ID and date."""
        logger.debug(f"Fetching attendance for employee {employee_id} on {attendance_date}")
        try:
            record = self.db.query(EmployeeAvailability).filter(
                EmployeeAvailability.employee_id == employee_id,
                EmployeeAvailability.attendance_date == attendance_date
            ).first()
            return record
        except Exception as e:
            logger.error(f"Error fetching attendance for employee {employee_id} on {attendance_date}: {str(e)}")
            raise
    
    def create(self, attendance_data: Dict[str, Any], updated_by_id: int) -> EmployeeAvailability:
        """Create a new attendance record."""
        logger.info(f"Creating attendance for employee {attendance_data.get('employee_id')} on {attendance_data.get('attendance_date')}")
        
        try:
            # Check if record already exists
            existing = self.get_by_employee_date(
                attendance_data['employee_id'],
                attendance_data['attendance_date']
            )
            if existing:
                raise ValueError(f"Attendance already exists for employee {attendance_data['employee_id']} on {attendance_data['attendance_date']}")
            
            # Create record
            record = EmployeeAvailability(
                **attendance_data,
                updated_by_id=updated_by_id
            )
            
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            
            logger.info(f"Attendance created successfully: {record.attendance_id}")
            return record
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating attendance: {str(e)}")
            raise
    
    def update(self, attendance: EmployeeAvailability, update_data: Dict[str, Any], updated_by_id: int) -> EmployeeAvailability:
        """Update an existing attendance record."""
        logger.debug(f"Updating attendance: {attendance.attendance_id}")
        
        try:
            # Update fields
            for key, value in update_data.items():
                if value is not None and hasattr(attendance, key):
                    setattr(attendance, key, value)
            
            # Update metadata
            attendance.updated_by_id = updated_by_id
            
            self.db.commit()
            self.db.refresh(attendance)
            
            logger.debug(f"Attendance updated successfully: {attendance.attendance_id}")
            return attendance
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating attendance {attendance.attendance_id}: {str(e)}")
            raise
    
    def delete(self, attendance_id: int) -> bool:
        """Delete an attendance record."""
        logger.warning(f"Deleting attendance: {attendance_id}")
        
        try:
            record = self.get_by_id(attendance_id)
            if not record:
                logger.warning(f"Attendance not found for deletion: {attendance_id}")
                return False
            
            self.db.delete(record)
            self.db.commit()
            
            logger.warning(f"Attendance deleted successfully: {attendance_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting attendance {attendance_id}: {str(e)}")
            raise
    
    def search(self, filters: AttendanceFilter, skip: int = 0, limit: int = 100,
               sort_by: str = "attendance_date", sort_order: str = "desc") -> Tuple[List[EmployeeAvailability], int]:
        """Search attendance records with filters."""
        logger.debug(f"Searching attendance with filters: {filters.dict(exclude_none=True)}")
        
        try:
            query = self.db.query(EmployeeAvailability)
            
            # Apply filters
            if filters.employee_id:
                query = query.filter(EmployeeAvailability.employee_id == filters.employee_id)
            
            if filters.start_date:
                query = query.filter(EmployeeAvailability.attendance_date >= filters.start_date)
            
            if filters.end_date:
                query = query.filter(EmployeeAvailability.attendance_date <= filters.end_date)
            
            if filters.month and filters.year:
                query = query.filter(
                    extract('month', EmployeeAvailability.attendance_date) == filters.month,
                    extract('year', EmployeeAvailability.attendance_date) == filters.year
                )
            elif filters.month:
                query = query.filter(extract('month', EmployeeAvailability.attendance_date) == filters.month)
            elif filters.year:
                query = query.filter(extract('year', EmployeeAvailability.attendance_date) == filters.year)
            
            if filters.day_type:
                query = query.filter(EmployeeAvailability.day_type == filters.day_type.value)
            
            if filters.first_half:
                query = query.filter(EmployeeAvailability.first_half == filters.first_half.value)
            
            if filters.second_half:
                query = query.filter(EmployeeAvailability.second_half == filters.second_half.value)
            
            if filters.leave_status:
                query = query.filter(EmployeeAvailability.leave_status == filters.leave_status.value)
            
            if filters.shift_id:
                query = query.filter(EmployeeAvailability.shift_id == filters.shift_id)
            
            # Get total count before pagination
            total = query.count()
            
            # Apply sorting
            sort_column = getattr(EmployeeAvailability, sort_by, EmployeeAvailability.attendance_date)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Apply pagination
            records = query.offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(records)} attendance records (total: {total})")
            return records, total
            
        except Exception as e:
            logger.error(f"Error searching attendance: {str(e)}")
            raise
    
    def apply_leave(self, employee_id: int, attendance_date: date, half_type: str,
                   leave_applied_by_id: int, reason: Optional[str] = None,
                   comment_json: Optional[Dict] = None) -> EmployeeAvailability:
        """Apply for leave."""
        logger.info(f"Applying {half_type} leave for employee {employee_id} on {attendance_date}")
        
        try:
            # Get or create attendance record
            record = self.get_by_employee_date(employee_id, attendance_date)
            
            if not record:
                # Create new record for leave application
                record = EmployeeAvailability(
                    employee_id=employee_id,
                    attendance_date=attendance_date,
                    day_type=DayTypeEnum.WORKDAY,
                    shift_id=1,  # Default shift, should be parameterized
                    updated_by_id=leave_applied_by_id,
                    leave_applied_by_id=leave_applied_by_id,
                    leave_applied_at=datetime.utcnow(),
                    leave_status=LeaveStatusEnum.PENDING
                )
                self.db.add(record)
            
            # Update leave status based on half type
            if half_type == "first":
                record.first_half = HalfStatusEnum.LEAVE
            elif half_type == "second":
                record.second_half = HalfStatusEnum.LEAVE
            elif half_type == "full":
                record.first_half = HalfStatusEnum.LEAVE
                record.second_half = HalfStatusEnum.LEAVE
            
            # Update leave application details
            record.leave_applied_by_id = leave_applied_by_id
            record.leave_applied_at = datetime.utcnow()
            record.leave_status = LeaveStatusEnum.PENDING
            
            # Update comments
            if comment_json:
                if record.comment_json:
                    record.comment_json.update(comment_json)
                else:
                    record.comment_json = comment_json
            
            if reason and record.comment_json:
                record.comment_json['leave_reason'] = reason
            
            record.updated_by_id = leave_applied_by_id
            
            self.db.commit()
            self.db.refresh(record)
            
            logger.info(f"Leave applied successfully: {record.attendance_id}")
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error applying leave: {str(e)}")
            raise
    
    def process_leave_action(self, attendance_id: int, action: LeaveStatusEnum,
                           approved_by_id: int, comments: Optional[str] = None) -> EmployeeAvailability:
        """Approve or reject a leave request."""
        logger.info(f"Processing leave {action.value} for attendance {attendance_id}")
        
        try:
            record = self.get_by_id(attendance_id)
            if not record:
                raise ValueError(f"Attendance record not found: {attendance_id}")
            
            if record.leave_status != LeaveStatusEnum.PENDING:
                raise ValueError(f"Leave is not in pending status: {record.leave_status}")
            
            # Update leave status
            record.leave_status = action
            record.leave_approved_by_id = approved_by_id
            record.leave_approved_at = datetime.utcnow()
            record.updated_by_id = approved_by_id
            
            # Update comments
            if comments:
                if record.comment_json:
                    record.comment_json['approval_comments'] = comments
                else:
                    record.comment_json = {'approval_comments': comments}
            
            # If rejected, revert leave status to present
            if action == LeaveStatusEnum.REJECTED:
                if record.first_half == HalfStatusEnum.LEAVE:
                    record.first_half = HalfStatusEnum.PRESENT
                if record.second_half == HalfStatusEnum.LEAVE:
                    record.second_half = HalfStatusEnum.PRESENT
            
            self.db.commit()
            self.db.refresh(record)
            
            logger.info(f"Leave {action.value} processed successfully: {attendance_id}")
            return record
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing leave action: {str(e)}")
            raise
    
    def check_in(self, employee_id: int, check_in_location_id: int,
                check_in_time: Optional[datetime] = None,
                updated_by_id: int = None,
                comment_json: Optional[Dict] = None) -> EmployeeAvailability:
        """Record employee check-in."""
        logger.info(f"Recording check-in for employee {employee_id}")
        
        try:
            today = date.today()
            check_in_time = check_in_time or datetime.utcnow()
            
            # Get or create today's attendance record
            record = self.get_by_employee_date(employee_id, today)
            
            if not record:
                # Create new record
                record = EmployeeAvailability(
                    employee_id=employee_id,
                    attendance_date=today,
                    day_type=DayTypeEnum.WORKDAY,
                    first_half=HalfStatusEnum.PRESENT,
                    second_half=HalfStatusEnum.PRESENT,
                    shift_id=1,  # Default shift
                    updated_by_id=updated_by_id or employee_id
                )
                self.db.add(record)
            
            # Update check-in details
            record.check_in_time = check_in_time
            record.check_in_location_id = check_in_location_id
            record.updated_by_id = updated_by_id or employee_id
            
            # Update comments
            if comment_json:
                if record.comment_json:
                    record.comment_json.update(comment_json)
                else:
                    record.comment_json = comment_json
            
            self.db.commit()
            self.db.refresh(record)
            
            logger.info(f"Check-in recorded successfully: {record.attendance_id}")
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording check-in: {str(e)}")
            raise
    
    def check_out(self, employee_id: int, check_out_location_id: int,
                 check_out_time: Optional[datetime] = None,
                 updated_by_id: int = None,
                 comment_json: Optional[Dict] = None) -> EmployeeAvailability:
        """Record employee check-out."""
        logger.info(f"Recording check-out for employee {employee_id}")
        
        try:
            today = date.today()
            check_out_time = check_out_time or datetime.utcnow()
            
            # Get today's attendance record
            record = self.get_by_employee_date(employee_id, today)
            
            if not record:
                raise ValueError(f"No attendance record found for employee {employee_id} today")
            
            if not record.check_in_time:
                raise ValueError("Cannot check out without checking in first")
            
            # Update check-out details
            record.check_out_time = check_out_time
            record.check_out_location_id = check_out_location_id
            record.updated_by_id = updated_by_id or employee_id
            
            # Calculate work hours
            if record.check_in_time:
                work_hours = (check_out_time - record.check_in_time).total_seconds() / 3600
                record.total_workhours = round(work_hours, 2)
            
            # Update comments
            if comment_json:
                if record.comment_json:
                    record.comment_json.update(comment_json)
                else:
                    record.comment_json = comment_json
            
            self.db.commit()
            self.db.refresh(record)
            
            logger.info(f"Check-out recorded successfully: {record.attendance_id}")
            return record
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording check-out: {str(e)}")
            raise
    
    def get_monthly_summary(self, employee_id: int, month: int, year: int) -> Dict[str, Any]:
        """Get monthly attendance summary for an employee."""
        logger.debug(f"Getting monthly summary for employee {employee_id}, {month}/{year}")
        
        try:
            # Calculate date range
            import calendar
            _, last_day = calendar.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
            
            # Query attendance records
            records = self.db.query(EmployeeAvailability).filter(
                EmployeeAvailability.employee_id == employee_id,
                EmployeeAvailability.attendance_date >= start_date,
                EmployeeAvailability.attendance_date <= end_date
            ).all()
            
            # Calculate statistics
            total_days = len(records)
            present_days = 0
            leave_days = 0
            absent_days = 0
            weekoff_days = 0
            holiday_days = 0
            total_work_hours = 0
            
            for record in records:
                if record.day_type == DayTypeEnum.WEEKOFF:
                    weekoff_days += 1
                elif record.day_type == DayTypeEnum.HOLIDAY or record.day_type == DayTypeEnum.COMP_OFF:
                    holiday_days += 1
                elif record.first_half == HalfStatusEnum.PRESENT and record.second_half == HalfStatusEnum.PRESENT:
                    present_days += 1
                elif record.first_half == HalfStatusEnum.LEAVE or record.second_half == HalfStatusEnum.LEAVE:
                    leave_days += 1
                else:
                    absent_days += 1
                
                if record.total_workhours:
                    total_work_hours += float(record.total_workhours)
            
            avg_daily_hours = total_work_hours / present_days if present_days > 0 else 0
            
            return {
                'employee_id': employee_id,
                'month': month,
                'year': year,
                'total_days': total_days,
                'present_days': present_days,
                'leave_days': leave_days,
                'absent_days': absent_days,
                'weekoff_days': weekoff_days,
                'holiday_days': holiday_days,
                'total_work_hours': round(total_work_hours, 2),
                'avg_daily_hours': round(avg_daily_hours, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly summary: {str(e)}")
            raise