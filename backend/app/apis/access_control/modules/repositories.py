# app/apis/modules/repositories.py
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func

from .models import Module

logger = logging.getLogger(__name__)


class ModuleRepository:
    """Repository for Module database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, module_id: int) -> Optional[Module]:
        """Get module by ID."""
        logger.debug(f"Fetching module by ID: {module_id}")
        try:
            module = self.db.query(Module).filter(Module.module_id == module_id).first()
            return module
        except Exception as e:
            logger.error(f"Error fetching module by ID {module_id}: {str(e)}")
            raise
    
    def get_by_name(self, module_name: str) -> Optional[Module]:
        """Get module by name."""
        logger.debug(f"Fetching module by name: {module_name}")
        try:
            module = self.db.query(Module).filter(Module.module_name == module_name.title()).first()
            return module
        except Exception as e:
            logger.error(f"Error fetching module by name {module_name}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Module]:
        """Get all modules with pagination."""
        logger.debug(f"Fetching all modules (skip: {skip}, limit: {limit})")
        try:
            modules = self.db.query(Module).offset(skip).limit(limit).all()
            return modules
        except Exception as e:
            logger.error(f"Error fetching all modules: {str(e)}")
            raise
    
    def create(self, module_data: Dict[str, Any], updated_by: int) -> Module:
        """Create a new module."""
        logger.info(f"Creating new module: {module_data.get('module_name')}")
        
        try:
            # Check if module already exists
            existing = self.get_by_name(module_data['module_name'])
            if existing:
                raise ValueError(f"Module already exists: {module_data['module_name']}")
            
            # Create module
            module = Module(**module_data)
            module.updated_by = updated_by
            
            self.db.add(module)
            self.db.commit()
            self.db.refresh(module)
            
            logger.info(f"Module created successfully: {module.module_id}")
            return module
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating module: {str(e)}")
            raise
    
    def update(self, module: Module, update_data: Dict[str, Any], updated_by: int) -> Module:
        """Update an existing module."""
        logger.debug(f"Updating module: {module.module_id}")
        
        try:
            # Check for duplicate module_name if being changed
            if 'module_name' in update_data and update_data['module_name'] != module.module_name:
                existing = self.get_by_name(update_data['module_name'])
                if existing and existing.module_id != module.module_id:
                    raise ValueError(f"Module name already exists: {update_data['module_name']}")
            
            # Update fields
            for key, value in update_data.items():
                if value is not None and hasattr(module, key):
                    setattr(module, key, value)
            
            # Update metadata
            module.updated_by = updated_by
            
            self.db.commit()
            self.db.refresh(module)
            
            logger.debug(f"Module updated successfully: {module.module_id}")
            return module
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating module {module.module_id}: {str(e)}")
            raise
    
    def delete(self, module_id: int) -> bool:
        """Delete a module."""
        logger.warning(f"Deleting module: {module_id}")
        
        try:
            module = self.get_by_id(module_id)
            if not module:
                return False
            
            self.db.delete(module)
            self.db.commit()
            
            logger.warning(f"Module deleted successfully: {module_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting module {module_id}: {str(e)}")
            raise
    
    def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Module]:
        """Search modules by name."""
        logger.debug(f"Searching modules: {search_term}")
        
        try:
            query = self.db.query(Module)
            
            if search_term:
                search = f"%{search_term}%"
                query = query.filter(Module.module_name.ilike(search))
            
            modules = query.offset(skip).limit(limit).all()
            return modules
            
        except Exception as e:
            logger.error(f"Error searching modules: {str(e)}")
            raise
    
    def get_count(self) -> int:
        """Get total module count."""
        logger.debug("Getting module count")
        try:
            count = self.db.query(func.count(Module.module_id)).scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting module count: {str(e)}")
            raise