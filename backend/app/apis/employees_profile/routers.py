import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.apis.auth.repositories import UserRepository
from app.apis.auth.services import AuthService
from .repositories import EmployeeProfileRepository, EmployeeDocumentRepository
from .services import EmployeeProfileService
from .schemas import (
    EmployeeProfileCreate,
    EmployeeProfileUpdate,
    EmployeeProfileResponse,
    EmployeeProfileDetailResponse,
    EmployeeListResponse,
    EmployeeDocumentResponse
)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/employees", tags=["Employees"])


# ========== DEPENDENCY INJECTION ==========

def get_employee_repository(db: Session = Depends(get_db)) -> EmployeeProfileRepository:
    return EmployeeProfileRepository(db)


def get_document_repository(db: Session = Depends(get_db)) -> EmployeeDocumentRepository:
    return EmployeeDocumentRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_employee_service(
    employee_repo: EmployeeProfileRepository = Depends(get_employee_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    doc_repo: EmployeeDocumentRepository = Depends(get_document_repository)
) -> EmployeeProfileService:
    return EmployeeProfileService(employee_repo, user_repo, doc_repo)


# Create a proper dependency for current_user
def get_current_user_dependency(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Dependency to get current user."""
    auth_service = AuthService(user_repo)
    return auth_service.get_current_user(request)


# ========== MIDDLEWARE ==========

async def verify_employee_access(
    request: Request,  # MUST BE FIRST - no default value
    employee_id: int,
    current_user = Depends(get_current_user_dependency),
    employee_service: EmployeeProfileService = Depends(get_employee_service),
    db: Session = Depends(get_db)
):
    """Verify if current user has access to employee data."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(current_user.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Admins can access all employees
    if user.is_admin:
        return
    
    # Users can only access their own profile
    employee = employee_service.employee_repo.get_by_user_id(user.id)
    if not employee or employee.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )


# ========== ROUTES ==========

@router.get("/", response_model=EmployeeListResponse)
async def get_employees(
    request: Request,  # ✅ FIRST: No default value parameters first
    current_user = Depends(get_current_user_dependency),  # ✅ Use correct dependency
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    employee_service: EmployeeProfileService = Depends(get_employee_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get all employees with pagination and filtering.
    """
    logger.info("Get employees endpoint called")
    
    # Check if user is admin
    user = user_repo.get_by_email(current_user.email)
    
    if not user.is_admin:
        # Non-admin users can only see their own profile
        employee = employee_service.employee_repo.get_by_user_id(user.id)
        if employee:
            items = [EmployeeProfileResponse.from_orm(employee)]
            return EmployeeListResponse(
                items=items,
                total=1,
                page=1,
                size=1,
                pages=1
            )
        return EmployeeListResponse(
            items=[],
            total=0,
            page=1,
            size=limit,
            pages=0
        )
    
    # Admin users get full list
    return employee_service.get_employees(
        skip=skip,
        limit=min(limit, 100),
        search=search,
        department=department,
        status=status
    )


@router.get("/{employee_id}", response_model=EmployeeProfileDetailResponse)
async def get_employee(
    request: Request,  # ✅ ADD THIS
    employee_id: int,
    _ = Depends(verify_employee_access),  # ✅ Now has request via verify_employee_access
    employee_service: EmployeeProfileService = Depends(get_employee_service)
):
    """
    Get employee profile by ID.
    """
    logger.info(f"Get employee endpoint called for ID: {employee_id}")
    return employee_service.get_employee_by_id(employee_id)


@router.get("/user/{user_id}", response_model=EmployeeProfileResponse)
async def get_employee_by_user(
    request: Request,  # ✅ ADD THIS FIRST
    user_id: int,
    current_user = Depends(get_current_user_dependency),  # ✅ FIXED: Use correct dependency
    employee_service: EmployeeProfileService = Depends(get_employee_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get employee profile by user ID.
    """
    logger.info(f"Get employee by user endpoint called for user ID: {user_id}")
    
    # Check access
    current_user_obj = user_repo.get_by_email(current_user.email)
    
    if not current_user_obj.is_admin and current_user_obj.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return employee_service.get_employee_by_user_id(user_id)


@router.post("/", response_model=EmployeeProfileResponse)
async def create_employee(
    request: Request,  # ✅ ADD THIS FIRST
    employee_data: EmployeeProfileCreate,
    current_user = Depends(get_current_user_dependency),  # ✅ FIXED: Use correct dependency
    employee_service: EmployeeProfileService = Depends(get_employee_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Create new employee profile.
    """
    logger.info("Create employee endpoint called")
    
    # Check if user is admin
    user = user_repo.get_by_email(current_user.email)
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return employee_service.create_employee(employee_data)


@router.put("/{employee_id}", response_model=EmployeeProfileResponse)
async def update_employee(
    request: Request,  # ✅ ADD THIS FIRST
    employee_id: int,
    update_data: EmployeeProfileUpdate,
    _ = Depends(verify_employee_access),  # ✅ Now has request via verify_employee_access
    employee_service: EmployeeProfileService = Depends(get_employee_service)
):
    """
    Update employee profile.
    """
    logger.info(f"Update employee endpoint called for ID: {employee_id}")
    return employee_service.update_employee(employee_id, update_data)


@router.delete("/{employee_id}")
async def delete_employee(
    request: Request,  # ✅ ADD THIS FIRST
    employee_id: int,
    current_user = Depends(get_current_user_dependency),  # ✅ FIXED: Use correct dependency
    employee_service: EmployeeProfileService = Depends(get_employee_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Delete employee profile (soft delete).
    """
    logger.info(f"Delete employee endpoint called for ID: {employee_id}")
    
    # Check if user is admin
    user = user_repo.get_by_email(current_user.email)
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return employee_service.delete_employee(employee_id)


@router.post("/{employee_id}/documents", response_model=EmployeeDocumentResponse)
async def upload_employee_document(
    request: Request,  # ✅ ADD THIS FIRST
    employee_id: int,
    document_type: str = Form(...),
    document_name: str = Form(...),
    file: UploadFile = File(...),
    current_user = Depends(get_current_user_dependency),  # ✅ FIXED: Use correct dependency
    employee_service: EmployeeProfileService = Depends(get_employee_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Upload document for employee.
    """
    logger.info(f"Upload document endpoint called for employee: {employee_id}")
    
    # Check access
    user = user_repo.get_by_email(current_user.email)
    
    if not user.is_admin:
        employee = employee_service.employee_repo.get_by_user_id(user.id)
        if not employee or employee.id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return employee_service.upload_document(
        employee_id=employee_id,
        document_type=document_type,
        document_name=document_name,
        file=file,
        uploaded_by=user.id
    )


@router.get("/{employee_id}/documents", response_model=list[EmployeeDocumentResponse])
async def get_employee_documents(
    request: Request,  # ✅ ADD THIS FIRST
    employee_id: int,
    _ = Depends(verify_employee_access),  # ✅ Now has request via verify_employee_access
    employee_service: EmployeeProfileService = Depends(get_employee_service)
):
    """
    Get all documents for an employee.
    """
    logger.info(f"Get documents endpoint called for employee: {employee_id}")
    return employee_service.get_employee_documents(employee_id)


# ========== DEBUG ENDPOINT ==========
@router.get("/test/auth")
async def test_auth(
    request: Request,
    current_user = Depends(get_current_user_dependency)
):
    """Test endpoint to verify authentication works."""
    return {
        "status": "success",
        "user": current_user.email,
        "message": "Authentication is working!"
    }