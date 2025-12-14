# app/apis/users/routes.py
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from .repositories import UserRepository
from .services import UserService
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserProfileResponse, UserFilter, UserBulkUpdate
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/users", tags=["Users"])


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


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(user_repo)


@router.get("/", response_model=UserListResponse)
async def get_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all users with pagination.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Number of records to return (max 1000)
    - Returns: List of users with pagination info
    """
    logger.info("Get all users endpoint called")
    return user_service.get_users(request, skip=skip, limit=limit)


@router.get("/search", response_model=UserListResponse)
async def search_users(
    request: Request,
    search: Optional[str] = Query(None, description="Search term (name, email, employee ID, phone)"),
    status: Optional[str] = Query(None, description="User status filter"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    vertical_id: Optional[int] = Query(None, description="Filter by vertical ID"),
    designation_id: Optional[int] = Query(None, description="Filter by designation ID"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    date_of_joining_from: Optional[str] = Query(None, description="Date of joining from (YYYY-MM-DD)"),
    date_of_joining_to: Optional[str] = Query(None, description="Date of joining to (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    sort_by: str = Query("user_id", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Search users with filters.
    
    - **search**: Search in name, email, employee ID, phone
    - **status**: Filter by status (active/inactive/terminated/suspended)
    - **team_id**: Filter by team
    - **vertical_id**: Filter by vertical
    - **designation_id**: Filter by designation
    - **role_id**: Filter by role
    - **is_active**: Filter by active status
    - **is_admin**: Filter by admin status
    - **date_of_joining_from**: Filter by joining date range
    - **date_of_joining_to**: Filter by joining date range
    - **sort_by**: Field to sort by
    - **sort_order**: Sort order
    - Returns: Filtered and sorted users with pagination
    """
    logger.info("Search users endpoint called")
    
    # Create filter object
    filters = UserFilter(
        search=search,
        status=status,
        team_id=team_id,
        vertical_id=vertical_id,
        designation_id=designation_id,
        role_id=role_id,
        is_active=is_active,
        is_admin=is_admin,
        date_of_joining_from=date_of_joining_from,
        date_of_joining_to=date_of_joining_to
    )
    
    return user_service.search_users(
        filters=filters,
        request=request,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    request: Request,
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user.
    
    - **Requires**: Admin privileges
    - **Request Body**: User data
    - Returns: Created user
    """
    logger.info("Create user endpoint called")
    return user_service.create_user(user_data, request)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID.
    
    - **user_id**: User ID
    - Returns: User details
    """
    logger.info(f"Get user endpoint called for ID: {user_id}")
    return user_service.get_user(user_id, request)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: Request,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user by ID.
    
    - **user_id**: User ID
    - **Request Body**: User data to update
    - Returns: Updated user
    """
    logger.info(f"Update user endpoint called for ID: {user_id}")
    return user_service.update_user(user_id, user_data, request)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user by ID.
    
    - **user_id**: User ID
    - **Requires**: Admin privileges
    - Returns: Success message
    """
    logger.info(f"Delete user endpoint called for ID: {user_id}")
    return user_service.delete_user(user_id, request)


@router.post("/bulk-update")
async def bulk_update_users(
    request: Request,
    bulk_data: UserBulkUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Update multiple users at once.
    
    - **Requires**: Admin privileges
    - **Request Body**: List of user IDs and fields to update
    - Returns: Update statistics
    """
    logger.info("Bulk update users endpoint called")
    return user_service.bulk_update_users(bulk_data, request)


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user profile with extended information.
    
    - **user_id**: User ID
    - Returns: User profile with manager names
    """
    logger.info(f"Get user profile endpoint called for ID: {user_id}")
    return user_service.get_user_profile(user_id, request)


@router.post("/{user_id}/resume")
async def upload_resume(
    user_id: int,
    request: Request,
    resume_file: UploadFile = File(...),
    user_service: UserService = Depends(get_user_service)
):
    """
    Upload/update user resume.
    
    - **user_id**: User ID
    - **resume_file**: Resume file (PDF/DOC/DOCX)
    - Returns: Upload details
    """
    logger.info(f"Upload resume endpoint called for user ID: {user_id}")
    return await user_service.update_user_resume(user_id, resume_file, request)


@router.get("/stats/counts")
async def get_user_counts(
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user statistics.
    
    - **Requires**: Admin privileges
    - Returns: User counts and statistics
    """
    logger.info("Get user counts endpoint called")
    return user_service.get_user_counts(request)


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user's profile.
    
    - Returns: Current user's profile with extended information
    """
    logger.info("Get my profile endpoint called")
    
    # Extract current user ID from token
    auth_header = request.headers.get("Authorization")
    access_token = user_service.get_current_user_id(request)
    
    return user_service.get_user_profile(access_token, request)


@router.put("/me/update")
async def update_my_profile(
    request: Request,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user's profile.
    
    - **Request Body**: User data to update
    - Returns: Updated user profile
    """
    logger.info("Update my profile endpoint called")
    
    # Extract current user ID from token
    current_user_id = user_service.get_current_user_id(request)
    
    return user_service.update_user(current_user_id, user_data, request)