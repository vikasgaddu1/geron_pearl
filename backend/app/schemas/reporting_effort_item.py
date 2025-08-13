"""Pydantic schemas for ReportingEffortItem."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.reporting_effort_item import SourceType
from app.models.package_item import ItemType


class ReportingEffortItemBase(BaseModel):
    """Base schema for ReportingEffortItem."""
    
    reporting_effort_id: int = Field(..., description="ID of the parent reporting effort")
    source_type: Optional[SourceType] = Field(None, description="Source of the item: package, reporting_effort, custom, bulk_upload")
    source_id: Optional[int] = Field(None, description="ID of the source (package_id or reporting_effort_id)")
    source_item_id: Optional[int] = Field(None, description="ID of the source item (package_item_id or reporting_effort_item_id)")
    item_type: ItemType = Field(..., description="Type of item: TLF or Dataset")
    item_subtype: str = Field(..., description="Subtype: Table/Listing/Figure for TLF, SDTM/ADaM for Dataset")
    item_code: str = Field(..., min_length=1, max_length=255, description="TLF ID or dataset name")
    is_active: bool = Field(True, description="Whether the item is active")


class ReportingEffortItemCreate(ReportingEffortItemBase):
    """Schema for creating a ReportingEffortItem."""
    pass


class ReportingEffortItemUpdate(BaseModel):
    """Schema for updating a ReportingEffortItem."""
    
    item_subtype: Optional[str] = None
    item_code: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class ReportingEffortItemInDB(ReportingEffortItemBase):
    """Schema for ReportingEffortItem from database."""
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReportingEffortItem(ReportingEffortItemInDB):
    """Schema for ReportingEffortItem response."""
    pass


class ReportingEffortItemWithDetails(ReportingEffortItemInDB):
    """Schema for ReportingEffortItem with all related details."""
    
    # Will be populated based on item_type
    tlf_details: Optional[dict] = None
    dataset_details: Optional[dict] = None
    footnotes: List[dict] = Field(default_factory=list)
    acronyms: List[dict] = Field(default_factory=list)
    tracker: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)