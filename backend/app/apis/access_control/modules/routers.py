# # app/apis/modules/routes.py
# import logging
# from typing import Optional
# from fastapi import APIRouter, Depends, Request, Query, HTTPException
# from sqlalchemy.orm import Session

# from app.database.session import SessionLocal
# from .repositories import ModuleRepository
# from .services import ModuleService
# from .schemas import ModuleCreate, ModuleUpdate, ModuleResponse, ModuleListResponse

# logger = logging.getLogger(__name__)

# # Create router
# router = APIRouter(prefix="/api/modules", tags=["Modules"])


# def get_db() -> Session:
#     """FastAPI dependency for database session."""
#     db = SessionLocal()
#     try:
#         yield db
#         db.commit()
#     except Exception:
#         db.rollback()
#         raise
#     finally:
#         db.close()


# def get_module_repository(db: Session = Depends(get_db)) -> ModuleRepository:
#     return ModuleRepository(db)


# def get_module_service(
#     module_repo: ModuleRepository = Depends(get_module_repository)
# ) -> ModuleService:
#     return ModuleService(module_repo)


# # **ESSENTIAL ENDPOINTS ONLY**

# @router.get("/", response_model=ModuleListResponse)
# async def get_modules(
#     request: Request,
#     skip: int = Query(0, ge=0, description="Number of records to skip"),
#     limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
#     module_service: ModuleService = Depends(get_module_service)
# ):
#     """
#     Get all modules with pagination.
    
#     - **skip**: Number of records to skip (pagination)
#     - **limit**: Number of records to return (max 1000)
#     - Returns: List of modules with pagination info
#     """
#     logger.info("Get all modules endpoint called")
#     return module_service.get_modules(request, skip=skip, limit=limit)


# @router.get("/search", response_model=ModuleListResponse)
# async def search_modules(
#     request: Request,
#     search: Optional[str] = Query(None, description="Search term for module name"),
#     skip: int = Query(0, ge=0, description="Number of records to skip"),
#     limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
#     module_service: ModuleService = Depends(get_module_service)
# ):
#     """
#     Search modules by name.
    
#     - **search**: Search term for module name
#     - Returns: Filtered modules with pagination info
#     """
#     logger.info("Search modules endpoint called")
#     return module_service.search_modules(search or "", request, skip=skip, limit=limit)


# @router.get("/{module_id}", response_model=ModuleResponse)
# async def get_module(
#     module_id: int,
#     request: Request,
#     module_service: ModuleService = Depends(get_module_service)
# ):
#     """
#     Get module by ID.
    
#     - **module_id**: Module ID
#     - Returns: Module details
#     """
#     logger.info(f"Get module endpoint called for ID: {module_id}")
#     return module_service.get_module(module_id, request)


# @router.post("/", response_model=ModuleResponse, status_code=201)
# async def create_module(
#     request: Request,
#     module_data: ModuleCreate,
#     module_service: ModuleService = Depends(get_module_service)
# ):
#     """
#     Create a new module.
    
#     - **Requires**: Admin privileges
#     - **Request Body**: Module data
#     - Returns: Created module
#     """
#     logger.info("Create module endpoint called")
#     return module_service.create_module(module_data, request)


# @router.put("/{module_id}", response_model=ModuleResponse)
# async def update_module(
#     module_id: int,
#     request: Request,
#     module_data: ModuleUpdate,
#     module_service: ModuleService = Depends(get_module_service)
# ):
#     """
#     Update module by ID.
    
#     - **module_id**: Module ID
#     - **Requires**: Admin privileges
#     - **Request Body**: Module data to update
#     - Returns: Updated module
#     """
#     logger.info(f"Update module endpoint called for ID: {module_id}")
#     return module_service.update_module(module_id, module_data, request)


# @router.delete("/{module_id}")
# async def delete_module(
#     module_id: int,
#     request: Request,
#     module_service: ModuleService = Depends(get_module_service)
# ):
#     """
#     Delete module by ID.
    
#     - **module_id**: Module ID
#     - **Requires**: Admin privileges
#     - Returns: Success message
#     """
#     logger.info(f"Delete module endpoint called for ID: {module_id}")
#     return module_service.delete_module(module_id, request)



# app/apis/access_control/modules/routes.py

from sqlalchemy.orm import Session


import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException

from app.database.session import SessionLocal
from .repositories import ModuleRepository
from .services import ModuleService
from .schemas import ModuleCreate, ModuleUpdate, ModuleResponse, ModuleListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/modules", tags=["Modules"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_module_repository(db: Session = Depends(get_db)) -> ModuleRepository:
    return ModuleRepository(db)


def get_module_service(
    module_repo: ModuleRepository = Depends(get_module_repository),
    db: Session = Depends(get_db)  # ✅ ADD THIS
) -> ModuleService:
    return ModuleService(module_repo, db)  # ✅ PASS DB TO SERVICE


# Routes remain the same but now with permission checks!
@router.get("/", response_model=ModuleListResponse)
async def get_modules(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    module_service: ModuleService = Depends(get_module_service)
):
    """Get all modules (requires module.view permission)"""
    return module_service.get_modules(request, skip=skip, limit=limit)


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: int,
    request: Request,
    module_service: ModuleService = Depends(get_module_service)
):
    """Get module by ID (requires module.view permission)"""
    return module_service.get_module(module_id, request)


@router.post("/", response_model=ModuleResponse, status_code=201)
async def create_module(
    request: Request,
    module_data: ModuleCreate,
    module_service: ModuleService = Depends(get_module_service)
):
    """Create new module (requires module.create permission)"""
    return module_service.create_module(module_data, request)


@router.put("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: int,
    request: Request,
    module_data: ModuleUpdate,
    module_service: ModuleService = Depends(get_module_service)
):
    """Update module (requires module.update permission)"""
    return module_service.update_module(module_id, module_data, request)


@router.delete("/{module_id}")
async def delete_module(
    module_id: int,
    request: Request,
    module_service: ModuleService = Depends(get_module_service)
):
    """Delete module (requires module.delete permission)"""
    return module_service.delete_module(module_id, request)