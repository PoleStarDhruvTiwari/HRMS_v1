from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel


T = TypeVar("T")


class SuccessResponse(GenericModel, Generic[T]):
    """Standard success response model."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: bool = True
    message: str
    error_code: Optional[str] = None
    details: Optional[List[Dict[str, Any]]] = None


class PaginatedResponse(GenericModel, Generic[T]):
    """Standard paginated response model."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


# Helper functions
def create_success_response(
    data: Any = None,
    message: str = None,
    meta: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {"success": True}
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    if meta:
        response["meta"] = meta
    
    return response


def create_error_response(
    message: str,
    error_code: str = None,
    details: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    response = {
        "error": True,
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return response