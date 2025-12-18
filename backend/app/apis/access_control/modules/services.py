# app/apis/modules/services.py
import logging
from typing import List, Optional
from fastapi import HTTPException, status

from app.core.security import security_service
from .repositories import ModuleRepository
from .schemas import ModuleCreate, ModuleUpdate, ModuleResponse, ModuleListResponse

logger = logging.getLogger(__name__)


class ModuleService:
    """Service for module business logic."""
    
    def __init__(self, module_repo: ModuleRepository):
        self.module_repo = module_repo
    
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
        from app.database.session import SessionLocal
        from app.apis.users.repositories import UserRepository
        
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            user = user_repo.get_by_id(user_id)
            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
        finally:
            db.close()
    
    def get_module(self, module_id: int, request) -> ModuleResponse:
        """Get module by ID."""
        logger.debug(f"Getting module: {module_id}")
        
        try:
            self.get_current_user_id(request)  # Just for auth check
            
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
            self.get_current_user_id(request)  # Just for auth check
            
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
            self.verify_admin_access(current_user_id)
            
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
            self.verify_admin_access(current_user_id)
            
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
            self.verify_admin_access(current_user_id)
            
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
            self.get_current_user_id(request)  # Just for auth check
            
            modules = self.module_repo.search(search_term, skip=skip, limit=limit)
            total = len(modules)  # Note: This is filtered count, not total
            
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