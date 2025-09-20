"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base schemas
class ProspectusBase(BaseModel):
    """Base schema for prospectus data."""
    filename: str
    file_path: str
    title: Optional[str] = None
    agency: Optional[str] = None
    location: Optional[str] = None
    square_footage: Optional[int] = None
    lease_term: Optional[str] = None
    budget: Optional[float] = None
    requirements: Optional[str] = None

class ProspectusCreate(ProspectusBase):
    """Schema for creating a new prospectus."""
    pass

class ProspectusResponse(ProspectusBase):
    """Schema for prospectus API responses."""
    id: int
    parsed_data: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class GSAPropertyBase(BaseModel):
    """Base schema for GSA property data."""
    gsa_id: str
    property_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    county: Optional[str] = None
    square_footage: Optional[int] = None
    building_type: Optional[str] = None
    lease_status: Optional[str] = None
    lease_expiry: Optional[datetime] = None
    monthly_rent: Optional[float] = None
    annual_rent: Optional[float] = None
    rent_per_sqft: Optional[float] = None
    agency: Optional[str] = None
    contact_info: Optional[str] = None
    description: Optional[str] = None
    amenities: Optional[str] = None
    parking_spaces: Optional[int] = None

class GSAPropertyCreate(GSAPropertyBase):
    """Schema for creating a new GSA property record."""
    pass

class GSAPropertyResponse(GSAPropertyBase):
    """Schema for GSA property API responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PropertyMatchBase(BaseModel):
    """Base schema for property match data."""
    prospectus_id: int
    gsa_property_id: int
    match_score: float = Field(..., ge=0, le=100)
    match_reasons: Optional[str] = None
    location_match: bool = False
    size_match: bool = False
    budget_match: bool = False
    requirements_match: bool = False
    status: str = "pending"
    notes: Optional[str] = None

class PropertyMatchCreate(PropertyMatchBase):
    """Schema for creating a new property match."""
    pass

class PropertyMatchResponse(PropertyMatchBase):
    """Schema for property match API responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    prospectus: Optional[ProspectusResponse] = None
    gsa_property: Optional[GSAPropertyResponse] = None
    
    class Config:
        from_attributes = True

class ExportBase(BaseModel):
    """Base schema for export data."""
    filename: str
    file_path: str
    export_type: Optional[str] = None
    record_count: Optional[int] = None
    filters_applied: Optional[str] = None
    created_by: Optional[str] = None

class ExportCreate(ExportBase):
    """Schema for creating a new export record."""
    pass

class ExportResponse(ExportBase):
    """Schema for export API responses."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Search and filter schemas
class PropertySearchFilters(BaseModel):
    """Schema for property search filters."""
    location: Optional[str] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    agency: Optional[str] = None
    building_type: Optional[str] = None
    lease_status: Optional[str] = None

class MatchFilters(BaseModel):
    """Schema for match filtering."""
    min_score: Optional[float] = Field(None, ge=0, le=100)
    status: Optional[str] = None
    prospectus_id: Optional[int] = None
    location_match: Optional[bool] = None
    size_match: Optional[bool] = None
    budget_match: Optional[bool] = None

# API response schemas
class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    """Paginated API response wrapper."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
