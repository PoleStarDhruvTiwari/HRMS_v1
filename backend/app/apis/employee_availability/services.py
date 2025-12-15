# app/apis/attendance/services.py
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import HTTPException, status

from app.core.security import security_service
from .repositories import AttendanceRepository
from .schemas import (
    EmployeeAvailabilityCreate, EmployeeAvailabilityUpdate, EmployeeAvailabilityResponse,
    AttendanceListResponse, AttendanceFilter, LeaveApplyRequest, LeaveActionRequest,
    CheckInRequest, CheckOutRequest, AttendanceSummaryResponse, AttendanceStatsResponse
)

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for attendance business logic."""
    
    def __init__(self, attendance_repo: AttendanceRepository):
        self.attendance_repo = attendance_repo
    
    def get_current_user_id(self, request) -> int:
        """Extract current user ID from request."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        access_token = security_service.extract_token_from_header(auth_header)
        payload = security_service.verify_local_token(access_token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return user_id
    
    def verify_admin_access(self, user_id: int):
        """Verify user has admin privileges."""
        # You'll need to import your user repository here
        # For now, we'll skip this check or implement as needed
        pass
    
    def verify_employee_access(self, user_id: int, employee_id: int):
        """Verify user can access employee data."""
        # User can access their own data, admin can access any
        if user_id != employee_id:
            self.verify_admin_access(user_id)
    
    def get_attendance(self, attendance_id: int, request) -> EmployeeAvailabilityResponse:
        """Get attendance by ID."""
        logger.debug(f"Getting attendance: {attendance_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            record = self.attendance_repo.get_by_id(attendance_id)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Attendance record not found"
                )
            
            # Verify access
            self.verify_employee_access(current_user_id, record.employee_id)
            
            # Convert to response
            response_data = {
                'attendance_id': record.attendance_id,
                'employee_id': record.employee_id,
                'attendance_date': record.attendance_date,
                'day_type': record.day_type.value,
                'first_half': record.first_half.value,
                'second_half': record.second_half.value,
                'check_in_time': record.check_in_time,
                'check_in_location_id': record.check_in_location_id,
                'check_out_time': record.check_out_time,
                'check_out_location_id': record.check_out_location_id,
                'total_workhours': float(record.total_workhours) if record.total_workhours else None,
                'shift_id': record.shift_id,
                'leave_applied_by_id': record.leave_applied_by_id,
                'leave_applied_at': record.leave_applied_at,
                'leave_status': record.leave_status.value if record.leave_status else None,
                'leave_approved_by_id': record.leave_approved_by_id,
                'leave_approved_at': record.leave_approved_at,
                'comment_json': record.comment_json,
                'updated_by_id': record.updated_by_id,
                'updated_at': record.updated_at,
                'created_at': record.created_at,
            }
            
            # Add related data if available
            if hasattr(record, 'employee') and record.employee:
                response_data['employee_name'] = record.employee.full_name
            
            return EmployeeAvailabilityResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting attendance {attendance_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_attendances(self, filters: AttendanceFilter, request, skip: int = 0, 
                       limit: int = 100, sort_by: str = "attendance_date", 
                       sort_order: str = "desc") -> AttendanceListResponse:
        """Search attendance records."""
        logger.debug(f"Getting attendances with filters")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # If employee_id is not specified and user is not admin, restrict to own records
            if not filters.employee_id:
                filters.employee_id = current_user_id
            else:
                # Verify access to requested employee data
                self.verify_employee_access(current_user_id, filters.employee_id)
            
            records, total = self.attendance_repo.search(
                filters=filters,
                skip=skip,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # Convert to responses
            attendance_responses = []
            for record in records:
                response_data = {
                    'attendance_id': record.attendance_id,
                    'employee_id': record.employee_id,
                    'attendance_date': record.attendance_date,
                    'day_type': record.day_type.value,
                    'first_half': record.first_half.value,
                    'second_half': record.second_half.value,
                    'check_in_time': record.check_in_time,
                    'check_in_location_id': record.check_in_location_id,
                    'check_out_time': record.check_out_time,
                    'check_out_location_id': record.check_out_location_id,
                    'total_workhours': float(record.total_workhours) if record.total_workhours else None,
                    'shift_id': record.shift_id,
                    'leave_applied_by_id': record.leave_applied_by_id,
                    'leave_applied_at': record.leave_applied_at,
                    'leave_status': record.leave_status.value if record.leave_status else None,
                    'leave_approved_by_id': record.leave_approved_by_id,
                    'leave_approved_at': record.leave_approved_at,
                    'comment_json': record.comment_json,
                    'updated_by_id': record.updated_by_id,
                    'updated_at': record.updated_at,
                    'created_at': record.created_at,
                }
                
                # Add related data if available
                if hasattr(record, 'employee') and record.employee:
                    response_data['employee_name'] = record.employee.full_name
                
                attendance_responses.append(EmployeeAvailabilityResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return AttendanceListResponse(
                attendances=attendance_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting attendances: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_attendance(self, attendance_data: EmployeeAvailabilityCreate, request) -> EmployeeAvailabilityResponse:
        """Create new attendance record."""
        logger.info(f"Creating attendance for employee {attendance_data.employee_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Verify access
            self.verify_employee_access(current_user_id, attendance_data.employee_id)
            
            # Convert to dict and create
            attendance_dict = attendance_data.dict(exclude_none=True)
            record = self.attendance_repo.create(attendance_dict, updated_by_id=current_user_id)
            
            # Return response
            return self.get_attendance(record.attendance_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating attendance: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_attendance(self, attendance_id: int, update_data: EmployeeAvailabilityUpdate, request) -> EmployeeAvailabilityResponse:
        """Update attendance record."""
        logger.info(f"Updating attendance: {attendance_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Get record
            record = self.attendance_repo.get_by_id(attendance_id)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Attendance record not found"
                )
            
            # Verify access
            self.verify_employee_access(current_user_id, record.employee_id)
            
            # Update record
            update_dict = update_data.dict(exclude_none=True)
            self.attendance_repo.update(record, update_dict, updated_by_id=current_user_id)
            
            # Return updated response
            return self.get_attendance(attendance_id, request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating attendance {attendance_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_attendance(self, attendance_id: int, request) -> Dict[str, str]:
        """Delete attendance record."""
        logger.warning(f"Deleting attendance: {attendance_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Get record
            record = self.attendance_repo.get_by_id(attendance_id)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Attendance record not found"
                )
            
            # Verify admin access for deletion
            self.verify_admin_access(current_user_id)
            
            # Delete record
            success = self.attendance_repo.delete(attendance_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Attendance record not found"
                )
            
            return {"message": "Attendance record deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting attendance {attendance_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def apply_leave(self, leave_data: LeaveApplyRequest, request) -> EmployeeAvailabilityResponse:
        """Apply for leave."""
        logger.info(f"Applying leave for employee {leave_data.employee_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Verify access (user can apply for their own leave, admin can apply for others)
            if leave_data.employee_id != current_user_id:
                self.verify_admin_access(current_user_id)
            
            # Apply leave
            record = self.attendance_repo.apply_leave(
                employee_id=leave_data.employee_id,
                attendance_date=leave_data.attendance_date,
                half_type=leave_data.half_type,
                leave_applied_by_id=current_user_id,
                reason=leave_data.reason,
                comment_json=leave_data.comment_json
            )
            
            # Return response
            return self.get_attendance(record.attendance_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error applying leave: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def process_leave_action(self, leave_action: LeaveActionRequest, request) -> EmployeeAvailabilityResponse:
        """Approve or reject leave."""
        logger.info(f"Processing leave action {leave_action.action} for attendance {leave_action.attendance_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Verify admin access for leave approval
            self.verify_admin_access(current_user_id)
            
            # Get record
            record = self.attendance_repo.get_by_id(leave_action.attendance_id)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Attendance record not found"
                )
            
            # Process leave action
            from .repositories import LeaveStatusEnum
            status_enum = LeaveStatusEnum(leave_action.action.value)
            
            record = self.attendance_repo.process_leave_action(
                attendance_id=leave_action.attendance_id,
                action=status_enum,
                approved_by_id=current_user_id,
                comments=leave_action.comments
            )
            
            # Return response
            return self.get_attendance(record.attendance_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error processing leave action: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def check_in(self, check_in_data: CheckInRequest, request) -> EmployeeAvailabilityResponse:
        """Record employee check-in."""
        logger.info(f"Recording check-in for employee {check_in_data.employee_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Verify access
            if check_in_data.employee_id != current_user_id:
                self.verify_admin_access(current_user_id)
            
            # Record check-in
            record = self.attendance_repo.check_in(
                employee_id=check_in_data.employee_id,
                check_in_location_id=check_in_data.check_in_location_id,
                check_in_time=check_in_data.check_in_time,
                updated_by_id=current_user_id,
                comment_json=check_in_data.comment_json
            )
            
            # Return response
            return self.get_attendance(record.attendance_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error recording check-in: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def check_out(self, check_out_data: CheckOutRequest, request) -> EmployeeAvailabilityResponse:
        """Record employee check-out."""
        logger.info(f"Recording check-out for employee {check_out_data.employee_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Verify access
            if check_out_data.employee_id != current_user_id:
                self.verify_admin_access(current_user_id)
            
            # Record check-out
            record = self.attendance_repo.check_out(
                employee_id=check_out_data.employee_id,
                check_out_location_id=check_out_data.check_out_location_id,
                check_out_time=check_out_data.check_out_time,
                updated_by_id=current_user_id,
                comment_json=check_out_data.comment_json
            )
            
            # Return response
            return self.get_attendance(record.attendance_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error recording check-out: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_monthly_summary(self, employee_id: int, month: int, year: int, request) -> AttendanceSummaryResponse:
        """Get monthly attendance summary."""
        logger.debug(f"Getting monthly summary for employee {employee_id}, {month}/{year}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Verify access
            self.verify_employee_access(current_user_id, employee_id)
            
            # Get summary
            summary = self.attendance_repo.get_monthly_summary(employee_id, month, year)
            
            return AttendanceSummaryResponse(**summary)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting monthly summary: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_today_attendance(self, employee_id: int, request) -> Optional[EmployeeAvailabilityResponse]:
        """Get today's attendance for employee."""
        logger.debug(f"Getting today's attendance for employee {employee_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # Verify access
            self.verify_employee_access(current_user_id, employee_id)
            
            # Get today's record
            today = date.today()
            record = self.attendance_repo.get_by_employee_date(employee_id, today)
            
            if record:
                return self.get_attendance(record.attendance_id, request)
            return None
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting today's attendance: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )