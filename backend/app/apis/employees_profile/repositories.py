import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from .models import EmployeeProfile, EmployeeDocument


logger = logging.getLogger(__name__)


class EmployeeProfileRepository:
    """Repository for EmployeeProfile database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, employee_id: int) -> Optional[EmployeeProfile]:
        """Get employee profile by ID."""
        logger.debug(f"Fetching employee profile by ID: {employee_id}")
        try:
            employee = self.db.query(EmployeeProfile).filter(
                EmployeeProfile.id == employee_id,
                EmployeeProfile.is_active == True
            ).first()
            
            if employee:
                logger.debug(f"Employee found: {employee.employee_id}")
            else:
                logger.debug(f"No employee found with ID: {employee_id}")
            
            return employee
        except Exception as e:
            logger.error(f"Error fetching employee by ID {employee_id}: {str(e)}")
            raise
    
    def get_by_user_id(self, user_id: int) -> Optional[EmployeeProfile]:
        """Get employee profile by user ID."""
        logger.debug(f"Fetching employee profile by user ID: {user_id}")
        try:
            employee = self.db.query(EmployeeProfile).filter(
                EmployeeProfile.user_id == user_id,
                EmployeeProfile.is_active == True
            ).first()
            
            if employee:
                logger.debug(f"Employee found for user {user_id}: {employee.employee_id}")
            else:
                logger.debug(f"No employee found for user ID: {user_id}")
            
            return employee
        except Exception as e:
            logger.error(f"Error fetching employee by user ID {user_id}: {str(e)}")
            raise
    
    def get_by_employee_id(self, employee_code: str) -> Optional[EmployeeProfile]:
        """Get employee profile by employee ID."""
        logger.debug(f"Fetching employee profile by employee ID: {employee_code}")
        try:
            employee = self.db.query(EmployeeProfile).filter(
                EmployeeProfile.employee_id == employee_code,
                EmployeeProfile.is_active == True
            ).first()
            
            if employee:
                logger.debug(f"Employee found: {employee_code}")
            else:
                logger.debug(f"No employee found with employee ID: {employee_code}")
            
            return employee
        except Exception as e:
            logger.error(f"Error fetching employee by employee ID {employee_code}: {str(e)}")
            raise
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[EmployeeProfile], int]:
        """Get all employee profiles with pagination and filtering."""
        logger.debug(f"Fetching employees: skip={skip}, limit={limit}")
        
        try:
            query = self.db.query(EmployeeProfile).filter(
                EmployeeProfile.is_active == True
            )
            
            # Apply filters
            if search:
                search_filter = or_(
                    EmployeeProfile.first_name.ilike(f"%{search}%"),
                    EmployeeProfile.last_name.ilike(f"%{search}%"),
                    EmployeeProfile.employee_id.ilike(f"%{search}%"),
                    EmployeeProfile.email.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
                logger.debug(f"Applied search filter: {search}")
            
            if department:
                query = query.filter(EmployeeProfile.department == department)
                logger.debug(f"Applied department filter: {department}")
            
            if status:
                query = query.filter(EmployeeProfile.employee_status == status)
                logger.debug(f"Applied status filter: {status}")
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            employees = query.offset(skip).limit(limit).all()
            
            logger.debug(f"Found {len(employees)} employees out of {total} total")
            return employees, total
            
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            raise
    
    def create(self, employee_data: dict) -> EmployeeProfile:
        """Create a new employee profile."""
        logger.info(f"Creating new employee profile: {employee_data.get('employee_id')}")
        
        try:
            # Check if employee_id already exists
            existing = self.get_by_employee_id(employee_data.get("employee_id"))
            if existing:
                logger.warning(f"Employee ID already exists: {employee_data.get('employee_id')}")
                raise ValueError(f"Employee ID {employee_data.get('employee_id')} already exists")
            
            employee = EmployeeProfile(**employee_data)
            
            self.db.add(employee)
            self.db.commit()
            self.db.refresh(employee)
            
            logger.info(f"Employee profile created: {employee.employee_id}")
            return employee
            
        except ValueError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating employee profile: {str(e)}")
            raise
    
    def update(self, employee_id: int, update_data: dict) -> Optional[EmployeeProfile]:
        """Update employee profile."""
        logger.info(f"Updating employee profile: {employee_id}")
        
        try:
            employee = self.get_by_id(employee_id)
            if not employee:
                logger.warning(f"Employee not found for update: {employee_id}")
                return None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(employee, key) and value is not None:
                    setattr(employee, key, value)
                    logger.debug(f"Updated {key} for employee {employee_id}")
            
            self.db.commit()
            self.db.refresh(employee)
            
            logger.info(f"Employee profile updated: {employee.employee_id}")
            return employee
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating employee profile {employee_id}: {str(e)}")
            raise
    
    def delete(self, employee_id: int) -> bool:
        """Soft delete employee profile."""
        logger.info(f"Deleting employee profile: {employee_id}")
        
        try:
            employee = self.get_by_id(employee_id)
            if not employee:
                logger.warning(f"Employee not found for deletion: {employee_id}")
                return False
            
            employee.is_active = False
            self.db.commit()
            
            logger.info(f"Employee profile deleted: {employee.employee_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting employee profile {employee_id}: {str(e)}")
            raise


class EmployeeDocumentRepository:
    """Repository for EmployeeDocument database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_employee(self, employee_id: int) -> List[EmployeeDocument]:
        """Get all documents for an employee."""
        logger.debug(f"Fetching documents for employee: {employee_id}")
        
        try:
            documents = self.db.query(EmployeeDocument).filter(
                EmployeeDocument.employee_id == employee_id
            ).all()
            
            logger.debug(f"Found {len(documents)} documents for employee {employee_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error fetching documents for employee {employee_id}: {str(e)}")
            raise
    
    def create(self, document_data: dict) -> EmployeeDocument:
        """Create a new employee document."""
        logger.info(f"Creating new document for employee: {document_data.get('employee_id')}")
        
        try:
            document = EmployeeDocument(**document_data)
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Document created: {document.document_name}")
            return document
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise
    
    def delete(self, document_id: int) -> bool:
        """Delete employee document."""
        logger.info(f"Deleting document: {document_id}")
        
        try:
            document = self.db.query(EmployeeDocument).filter(
                EmployeeDocument.id == document_id
            ).first()
            
            if not document:
                logger.warning(f"Document not found for deletion: {document_id}")
                return False
            
            self.db.delete(document)
            self.db.commit()
            
            logger.info(f"Document deleted: {document_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            raise