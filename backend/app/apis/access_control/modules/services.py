
# app/apis/access_control/modules/services.py
import logging
from typing import List
from fastapi import HTTPException, status

from app.core.base_service import BaseService
from .repositories import ModuleRepository
from .schemas import ModuleCreate, ModuleUpdate, ModuleResponse, ModuleListResponse

logger = logging.getLogger(__name__)


class ModuleService(BaseService):  # ✅ Inherit from BaseService
    """Service for module business logic."""
    
    def __init__(self, module_repo: ModuleRepository, db):
        super().__init__(db)  # ✅ Call parent constructor
        self.module_repo = module_repo
    
    def get_module(self, module_id: int, request) -> ModuleResponse:
        """Get module by ID."""
        logger.debug(f"Getting module: {module_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)  # ✅ From BaseService
            
            # ✅ PERMISSION CHECK ADDED HERE
            self.verify_permission(current_user_id, "module.view")
            
            module = self.module_repo.get_by_id(module_id)
            if not module:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Module not found"
                )
            
            # Convert to response
            response_data = {
                'module_id': module.module_id,
                'module_name': module.module_name,
                'updated_by': module.updated_by,
                'updated_at': module.updated_at,
            }
            
            # Add related data if available
            if hasattr(module, 'updater') and module.updater:
                response_data['updated_by_name'] = module.updater.full_name
            
            return ModuleResponse(**response_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting module {module_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_modules(self, request, skip: int = 0, limit: int = 100) -> ModuleListResponse:
        """Get all modules with pagination."""
        logger.debug(f"Getting modules (skip: {skip}, limit: {limit})")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # ✅ PERMISSION CHECK ADDED HERE
            self.verify_permission(current_user_id, "module.view")
            
            modules = self.module_repo.get_all(skip=skip, limit=limit)
            total = self.module_repo.get_count()
            
            # Convert to responses
            module_responses = []
            for module in modules:
                response_data = {
                    'module_id': module.module_id,
                    'module_name': module.module_name,
                    'updated_by': module.updated_by,
                    'updated_at': module.updated_at,
                }
                
                # Add related data if available
                if hasattr(module, 'updater') and module.updater:
                    response_data['updated_by_name'] = module.updater.full_name
                
                module_responses.append(ModuleResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return ModuleListResponse(
                modules=module_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting modules: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def create_module(self, module_data: ModuleCreate, request) -> ModuleResponse:
        """Create a new module."""
        logger.info(f"Creating new module: {module_data.module_name}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # ✅ PERMISSION CHECK ADDED HERE
            self.verify_permission(current_user_id, "module.create")
            
            # Convert to dict and create
            module_dict = module_data.dict()
            module = self.module_repo.create(module_dict, updated_by=current_user_id)
            
            return self.get_module(module.module_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error creating module: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def update_module(self, module_id: int, update_data: ModuleUpdate, request) -> ModuleResponse:
        """Update an existing module."""
        logger.info(f"Updating module: {module_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # ✅ PERMISSION CHECK ADDED HERE
            self.verify_permission(current_user_id, "module.update")
            
            # Get module
            module = self.module_repo.get_by_id(module_id)
            if not module:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Module not found"
                )
            
            # Update module
            update_dict = update_data.dict(exclude_none=True)
            self.module_repo.update(module, update_dict, updated_by=current_user_id)
            
            return self.get_module(module_id, request)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating module {module_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def delete_module(self, module_id: int, request) -> dict:
        """Delete a module."""
        logger.warning(f"Deleting module: {module_id}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # ✅ PERMISSION CHECK ADDED HERE
            self.verify_permission(current_user_id, "module.delete")
            
            # Check if module exists
            module = self.module_repo.get_by_id(module_id)
            if not module:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Module not found"
                )
            
            # Delete module
            success = self.module_repo.delete(module_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Module not found"
                )
            
            return {"message": "Module deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deleting module {module_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def search_modules(self, search_term: str, request, skip: int = 0, limit: int = 100) -> ModuleListResponse:
        """Search modules by name."""
        logger.debug(f"Searching modules: {search_term}")
        
        try:
            current_user_id = self.get_current_user_id(request)
            
            # ✅ PERMISSION CHECK ADDED HERE
            self.verify_permission(current_user_id, "module.view")
            
            modules = self.module_repo.search(search_term, skip=skip, limit=limit)
            total = len(modules)
            
            # Convert to responses
            module_responses = []
            for module in modules:
                response_data = {
                    'module_id': module.module_id,
                    'module_name': module.module_name,
                    'updated_by': module.updated_by,
                    'updated_at': module.updated_at,
                }
                
                # Add related data if available
                if hasattr(module, 'updater') and module.updater:
                    response_data['updated_by_name'] = module.updater.full_name
                
                module_responses.append(ModuleResponse(**response_data))
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (skip // limit) + 1 if limit > 0 else 1
            
            return ModuleListResponse(
                modules=module_responses,
                total=total,
                page=current_page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error searching modules: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )