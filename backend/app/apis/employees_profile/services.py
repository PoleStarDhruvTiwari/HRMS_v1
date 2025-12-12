import logging
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status, UploadFile, File
import os
from datetime import datetime

from .repositories import EmployeeProfileRepository, EmployeeDocumentRepository
from .schemas import (
    EmployeeProfileCreate,
    EmployeeProfileUpdate,
    EmployeeProfileResponse,
    EmployeeProfileDetailResponse,
    EmployeeListResponse,
    EmployeeDocumentResponse
)
from app.apis.auth.repositories import UserRepository


logger = logging.getLogger(__name__)


class EmployeeProfileService:
    """Service for employee profile business logic."""
    
    def __init__(
        self,
        employee_repo: EmployeeProfileRepository,
        user_repo: UserRepository,
        doc_repo: EmployeeDocumentRepository
    ):
        self.employee_repo = employee_repo
        self.user_repo = user_repo
        self.doc_repo = doc_repo
    
    def get_employee_by_id(self, employee_id: int) -> EmployeeProfileDetailResponse:
        """Get employee profile by ID."""
        logger.info(f"Getting employee profile by ID: {employee_id}")
        
        try:
            employee = self.employee_repo.get_by_id(employee_id)
            if not employee:
                logger.warning(f"Employee not found: {employee_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )
            
            # Get user details
            user = self.user_repo.get_by_email(employee.user.email) if employee.user else None
            
            response = EmployeeProfileDetailResponse.from_orm(employee)
            if user:
                response.user_email = user.email
                response.user_name = user.name
                response.user_picture = user.picture
            
            logger.info(f"Employee profile retrieved: {employee.employee_id}")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting employee {employee_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_employee_by_user_id(self, user_id: int) -> EmployeeProfileResponse:
        """Get employee profile by user ID."""
        logger.info(f"Getting employee profile by user ID: {user_id}")
        
        try:
            employee = self.employee_repo.get_by_user_id(user_id)
            if not employee:
                logger.warning(f"Employee not found for user: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee profile not found"
                )
            
            logger.info(f"Employee profile retrieved for user {user_id}: {employee.employee_id}")
            return EmployeeProfileResponse.from_orm(employee)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting employee for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_employees(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None
    ) -> EmployeeListResponse:
        """Get all employees with pagination and filtering."""
        logger.info(f"Getting employees: skip={skip}, limit={limit}")
        
        try:
            employees, total = self.employee_repo.get_all(
                skip=skip,
                limit=limit,
                search=search,
                department=department,
                status=status
            )
            
            # Calculate pagination info
            pages = (total + limit - 1) // limit if limit > 0 else 0
            
            response = EmployeeListResponse(
                items=[EmployeeProfileResponse.from_orm(emp) for emp in employees],
                total=total,
                page=skip // limit + 1 if limit > 0 else 1,
                size=limit,
                pages=pages
            )
            
            logger.info(f"Retrieved {len(employees)} employees")
            return response
            
        except Exception as e:
            logger.exception(f"Error getting employees: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_employee(self, employee_data: EmployeeProfileCreate) -> EmployeeProfileResponse:
        """Create new employee profile."""
        logger.info(f"Creating new employee: {employee_data.employee_id}")
        
        try:
            # Check if user exists
            user = self.user_repo.get_by_email(employee_data.user_id)
            if not user:
                logger.warning(f"User not found for employee creation: {employee_data.user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if employee already has a profile
            existing_profile = self.employee_repo.get_by_user_id(user.id)
            if existing_profile:
                logger.warning(f"User already has employee profile: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has an employee profile"
                )
            
            # Create employee profile
            employee_dict = employee_data.dict()
            employee_dict["user_id"] = user.id
            employee = self.employee_repo.create(employee_dict)
            
            logger.info(f"Employee profile created: {employee.employee_id}")
            return EmployeeProfileResponse.from_orm(employee)
            
        except ValueError as e:
            logger.warning(f"Validation error creating employee: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating employee: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_employee(
        self,
        employee_id: int,
        update_data: EmployeeProfileUpdate
    ) -> EmployeeProfileResponse:
        """Update employee profile."""
        logger.info(f"Updating employee: {employee_id}")
        
        try:
            # Remove None values from update data
            update_dict = {
                k: v for k, v in update_data.dict().items()
                if v is not None
            }
            
            if not update_dict:
                logger.warning("No update data provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No update data provided"
                )
            
            employee = self.employee_repo.update(employee_id, update_dict)
            if not employee:
                logger.warning(f"Employee not found for update: {employee_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )
            
            logger.info(f"Employee profile updated: {employee.employee_id}")
            return EmployeeProfileResponse.from_orm(employee)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating employee {employee_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_employee(self, employee_id: int) -> Dict[str, str]:
        """Delete employee profile (soft delete)."""
        logger.info(f"Deleting employee: {employee_id}")
        
        try:
            success = self.employee_repo.delete(employee_id)
            if not success:
                logger.warning(f"Employee not found for deletion: {employee_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )
            
            logger.info(f"Employee profile deleted: {employee_id}")
            return {"message": "Employee profile deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting employee {employee_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def upload_document(
        self,
        employee_id: int,
        document_type: str,
        document_name: str,
        file: UploadFile,
        uploaded_by: int
    ) -> EmployeeDocumentResponse:
        """Upload document for employee."""
        logger.info(f"Uploading document for employee: {employee_id}")
        
        try:
            # Check if employee exists
            employee = self.employee_repo.get_by_id(employee_id)
            if not employee:
                logger.warning(f"Employee not found for document upload: {employee_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )
            
            # Create upload directory if not exists
            upload_dir = f"uploads/employee_{employee_id}"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
            filename = f"{document_type}_{timestamp}{file_extension}"
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            # Get file size
            file_size = len(content)
            
            # Create document record
            document_data = {
                "employee_id": employee_id,
                "document_type": document_type,
                "document_name": document_name,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": file.content_type,
                "uploaded_by": uploaded_by
            }
            
            document = self.doc_repo.create(document_data)
            
            logger.info(f"Document uploaded: {document.document_name}")
            return EmployeeDocumentResponse.from_orm(document)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error uploading document: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_employee_documents(self, employee_id: int) -> List[EmployeeDocumentResponse]:
        """Get all documents for an employee."""
        logger.info(f"Getting documents for employee: {employee_id}")
        
        try:
            # Check if employee exists
            employee = self.employee_repo.get_by_id(employee_id)
            if not employee:
                logger.warning(f"Employee not found for document retrieval: {employee_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )
            
            documents = self.doc_repo.get_by_employee(employee_id)
            
            logger.info(f"Retrieved {len(documents)} documents for employee {employee_id}")
            return [EmployeeDocumentResponse.from_orm(doc) for doc in documents]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting documents for employee {employee_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )