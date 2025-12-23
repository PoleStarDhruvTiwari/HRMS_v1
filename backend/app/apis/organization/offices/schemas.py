# app/apis/organization/offices/schemas.py
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Base schemas
class OfficeBase(BaseModel):
    office_name: str = Field(..., min_length=2, max_length=150)
    latitude: Decimal = Field(..., ge=-90, le=90, decimal_places=6)
    longitude: Decimal = Field(..., ge=-180, le=180, decimal_places=6)
    
    @validator('office_name')
    def office_name_title_case(cls, v):
        return v.strip().title()
    
    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        return round(v, 6)


class OfficeCreate(OfficeBase):
    pass


class OfficeUpdate(BaseModel):
    office_name: Optional[str] = Field(None, min_length=2, max_length=150)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=6)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=6)
    
    @validator('office_name')
    def office_name_title_case(cls, v):
        if v:
            return v.strip().title()
        return v
    
    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        if v:
            return round(v, 6)
        return v
    
    class Config:
        extra = "forbid"


# Response schemas
class OfficeResponse(OfficeBase):
    office_id: int
    updated_by: int
    updated_at: Optional[datetime] = None
    updated_by_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class OfficeListResponse(BaseModel):
    offices: List[OfficeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Filter schemas
class OfficeFilter(BaseModel):
    search: Optional[str] = None
    office_name: Optional[str] = None


# Nearby offices search
class NearbyOfficeRequest(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90, decimal_places=6)
    longitude: Decimal = Field(..., ge=-180, le=180, decimal_places=6)
    radius_km: int = Field(10, ge=1, le=100)
    limit: int = Field(10, ge=1, le=50)


class NearbyOfficeResponse(OfficeResponse):
    distance_km: Optional[float] = None