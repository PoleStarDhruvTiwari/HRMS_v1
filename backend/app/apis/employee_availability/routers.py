# app/apis/attendance/routers.py
import logging
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Request, Query, HTTPException

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import AttendanceRepository
from .services import AttendanceService
from .schemas import (
    EmployeeAvailabilityCreate, EmployeeAvailabilityUpdate, EmployeeAvailabilityResponse,
    AttendanceListResponse, AttendanceFilter, LeaveApplyRequest, LeaveActionRequest,
    CheckInRequest, CheckOutRequest, AttendanceSummaryResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


def get_db() -> Session:
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_attendance_repository(db: Session = Depends(get_db)) -> AttendanceRepository:
    return AttendanceRepository(db)


def get_attendance_service(
    attendance_repo: AttendanceRepository = Depends(get_attendance_repository)
) -> AttendanceService:
    return AttendanceService(attendance_repo)


@router.get("/", response_model=AttendanceListResponse)
async def get_attendances(
    request: Request ,
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month filter (1-12)"),
    year: Optional[int] = Query(None, description="Year filter"),
    day_type: Optional[str] = Query(None, description="Day type filter"),
    first_half: Optional[str] = Query(None, description="First half status filter"),
    second_half: Optional[str] = Query(None, description="Second half status filter"),
    leave_status: Optional[str] = Query(None, description="Leave status filter"),
    shift_id: Optional[int] = Query(None, description="Shift ID filter"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    sort_by: str = Query("attendance_date", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Get filtered attendance records.
    """
    """
    Get attendance records with filters.
    
    - **employee_id**: Filter by employee
    - **start_date**: Start date range
    - **end_date**: End date range
    - **month**: Filter by month (1-12)
    - **year**: Filter by year
    - **day_type**: Filter by day type (workday/weekoff/holiday/comp-off holiday)
    - **first_half**: Filter by first half status (present/leave/absent)
    - **second_half**: Filter by second half status (present/leave/absent)
    - **leave_status**: Filter by leave status (pending/approved/rejected)
    - **shift_id**: Filter by shift ID
    - **sort_by**: Field to sort by
    - **sort_order**: Sort order
    - Returns: Filtered attendance records with pagination
    """
    logger.info("Get attendances endpoint called")
    
    # Create filter object
    filters = AttendanceFilter(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        month=month,
        year=year,
        day_type=day_type,
        first_half=first_half,
        second_half=second_half,
        leave_status=leave_status,
        shift_id=shift_id
    )
    
    return attendance_service.get_attendances(
        filters=filters,
        request=request,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/{attendance_id}", response_model=EmployeeAvailabilityResponse)
async def get_attendance(
    attendance_id: int,
    request: Request ,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Get attendance record by ID.
    
    - **attendance_id**: Attendance record ID
    - Returns: Attendance details
    """
    logger.info(f"Get attendance endpoint called for ID: {attendance_id}")
    return attendance_service.get_attendance(attendance_id, request)

@router.post("/", response_model=EmployeeAvailabilityResponse, status_code=201)
async def create_attendance(
    attendance_data: EmployeeAvailabilityCreate,
    request: Request ,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Create new attendance record.
    
    - **Requires**: Admin or self-access
    - **Request Body**: Attendance data
    - Returns: Created attendance record
    """
    logger.info("Create attendance endpoint called")
    return attendance_service.create_attendance(attendance_data, request)



@router.put("/{attendance_id}", response_model=EmployeeAvailabilityResponse)
async def update_attendance(
    attendance_id: int,
    request: Request,
    update_data: EmployeeAvailabilityUpdate,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Update attendance record.
    
    - **attendance_id**: Attendance record ID
    - **Request Body**: Attendance data to update
    - Returns: Updated attendance record
    """
    logger.info(f"Update attendance endpoint called for ID: {attendance_id}")
    return attendance_service.update_attendance(attendance_id, update_data, request)


@router.delete("/{attendance_id}")
async def delete_attendance(
    attendance_id: int,
    request: Request,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Delete attendance record.
    
    - **attendance_id**: Attendance record ID
    - **Requires**: Admin privileges
    - Returns: Success message
    """
    logger.info(f"Delete attendance endpoint called for ID: {attendance_id}")
    return attendance_service.delete_attendance(attendance_id, request)


@router.post("/apply-leave", response_model=EmployeeAvailabilityResponse)
async def apply_leave(
    request: Request,
    leave_data: LeaveApplyRequest,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Apply for leave.
    
    - **Request Body**: Leave application data
    - Returns: Updated attendance record
    """
    logger.info("Apply leave endpoint called")
    return attendance_service.apply_leave(leave_data, request)


@router.post("/process-leave", response_model=EmployeeAvailabilityResponse)
async def process_leave(
    request: Request,
    leave_action: LeaveActionRequest,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Approve or reject leave.
    
    - **Requires**: Admin privileges
    - **Request Body**: Leave action data
    - Returns: Updated attendance record
    """
    logger.info("Process leave endpoint called")
    return attendance_service.process_leave_action(leave_action, request)


@router.post("/check-in", response_model=EmployeeAvailabilityResponse)
async def check_in(
    request: Request,
    check_in_data: CheckInRequest,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Record employee check-in.
    
    - **Request Body**: Check-in data
    - Returns: Updated attendance record
    """
    logger.info("Check-in endpoint called")
    return attendance_service.check_in(check_in_data, request)


@router.post("/check-out", response_model=EmployeeAvailabilityResponse)
async def check_out(
    request: Request,
    check_out_data: CheckOutRequest,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Record employee check-out.
    
    - **Request Body**: Check-out data
    - Returns: Updated attendance record
    """
    logger.info("Check-out endpoint called")
    return attendance_service.check_out(check_out_data, request)


@router.get("/monthly-summary/{employee_id}")
async def get_monthly_summary(
    employee_id: int,
    request: Request,
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., description="Year"),
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Get monthly attendance summary for employee.
    
    - **employee_id**: Employee ID
    - **month**: Month (1-12)
    - **year**: Year
    - Returns: Monthly attendance summary
    """
    logger.info(f"Get monthly summary endpoint called for employee {employee_id}")
    return attendance_service.get_monthly_summary(employee_id, month, year, request)



@router.get("/today/{employee_id}", response_model=Optional[EmployeeAvailabilityResponse])
async def get_today_attendance(
    employee_id: int,
    request: Request,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Get today's attendance for employee.
    
    - **employee_id**: Employee ID
    - Returns: Today's attendance record or null
    """
    logger.info(f"Get today's attendance endpoint called for employee {employee_id}")
    return attendance_service.get_today_attendance(employee_id, request)


@router.get("/my-today", response_model=Optional[EmployeeAvailabilityResponse])
async def get_my_today_attendance(
    request: Request,
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Get current user's today attendance.
    
    - Returns: Today's attendance record for current user
    """
    logger.info("Get my today's attendance endpoint called")
    
    # Get current user ID from token
    current_user_id = attendance_service.get_current_user_id(request)
    return attendance_service.get_today_attendance(current_user_id, request)


# @router.post("/my-check-in", response_model=EmployeeAvailabilityResponse)
# async def my_check_in(
#     request: Request,
#     check_in_location_id: int = Query(..., description="Check-in location ID"),
#     attendance_service: AttendanceService = Depends(get_attendance_service)
# ):
#     """
#     Record current user's check-in.
    
#     - **check_in_location_id**: Check-in location ID
#     - Returns: Updated attendance record
#     """
#     logger.info("My check-in endpoint called")
    
#     # Get current user ID from token
#     current_user_id = attendance_service.get_current_user_id(request)
    
#     check_in_data = CheckInRequest(
#         employee_id=current_user_id,
#         check_in_location_id=check_in_location_id
#     )
    
#     return attendance_service.check_in(check_in_data, request)


# @router.post("/my-check-out", response_model=EmployeeAvailabilityResponse)
# async def my_check_out(
#     request: Request,
#     check_out_location_id: int = Query(..., description="Check-out location ID"),
#     attendance_service: AttendanceService = Depends(get_attendance_service)
# ):
#     """
#     Record current user's check-out.
    
#     - **check_out_location_id**: Check-out location ID
#     - Returns: Updated attendance record
#     """
#     logger.info("My check-out endpoint called")
    
#     # Get current user ID from token
#     current_user_id = attendance_service.get_current_user_id(request)
    
#     check_out_data = CheckOutRequest(
#         employee_id=current_user_id,
#         check_out_location_id=check_out_location_id
#     )
    
#     return attendance_service.check_out(check_out_data, request)

# Line ~246 - Fix my_check_in route

@router.post("/my-check-in", response_model=EmployeeAvailabilityResponse)
async def my_check_in(
    request: Request,
    check_in_location_id: int = Query(..., description="Check-in location ID"),
    attendance_service: AttendanceService = Depends(get_attendance_service),
):
    logger.info("My check-in endpoint called")

    current_user_id = attendance_service.get_current_user_id(request)

    check_in_data = CheckInRequest(
        employee_id=current_user_id,
        check_in_location_id=check_in_location_id,
    )

    return attendance_service.check_in(check_in_data, request)


@router.post("/my-check-out", response_model=EmployeeAvailabilityResponse)
async def my_check_out(
    request: Request,
    check_out_location_id: int = Query(..., description="Check-out location ID"),
    attendance_service: AttendanceService = Depends(get_attendance_service),
):
    logger.info("My check-out endpoint called")

    current_user_id = attendance_service.get_current_user_id(request)

    check_out_data = CheckOutRequest(
        employee_id=current_user_id,
        check_out_location_id=check_out_location_id,
    )

    return attendance_service.check_out(check_out_data, request)


@router.get("/my-monthly-summary")
async def get_my_monthly_summary(
    request: Request,
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., description="Year"),
    attendance_service: AttendanceService = Depends(get_attendance_service)
):
    """
    Get current user's monthly attendance summary.
    
    - **month**: Month (1-12)
    - **year**: Year
    - Returns: Monthly attendance summary
    """
    logger.info("Get my monthly summary endpoint called")
    
    # Get current user ID from token
    current_user_id = attendance_service.get_current_user_id(request)
    return attendance_service.get_monthly_summary(current_user_id, month, year, request)
