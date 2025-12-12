import logging
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)


class CustomHTTPException(StarletteHTTPException):
    """Custom HTTP exception with additional details."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = None,
        metadata: Dict[str, Any] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.metadata = metadata or {}


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    error_detail = {
        "error": True,
        "message": exc.detail,
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code
    }
    
    # Add additional details for custom exceptions
    if isinstance(exc, CustomHTTPException):
        if exc.error_code:
            error_detail["error_code"] = exc.error_code
        if exc.metadata:
            error_detail["metadata"] = exc.metadata
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} {exc.detail} "
        f"| Path: {request.url.path} | Method: {request.method}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_detail
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions."""
    error_detail = {
        "error": True,
        "message": "Validation error",
        "path": request.url.path,
        "method": request.method,
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "details": exc.errors()
    }
    
    logger.warning(
        f"Validation Error: {exc.errors()} "
        f"| Path: {request.url.path} | Method: {request.method}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_detail
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions."""
    error_detail = {
        "error": True,
        "message": "Internal server error",
        "path": request.url.path,
        "method": request.method,
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    logger.error(
        f"Unhandled Exception: {str(exc)} "
        f"| Path: {request.url.path} | Method: {request.method}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_detail
    )


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers for the application."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    logger.info("Exception handlers setup complete")