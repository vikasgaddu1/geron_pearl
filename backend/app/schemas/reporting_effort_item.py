"""Pydantic schemas for ReportingEffortItem."""

from typing import Optional, List
from datetime import datetime
# from enum import Enum  # No longer needed
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.enums import SourceType, ItemType


class ReportingEffortItemBase(BaseModel):
    """Base schema for ReportingEffortItem."""
    
    reporting_effort_id: int = Field(..., gt=0, description="ID of the parent reporting effort")
    source_type: Optional[str] = Field(None, description="Source of the item: package, reporting_effort, custom, bulk_upload")
    source_id: Optional[int] = Field(None, description="ID of the source (package_id or reporting_effort_id)")
    source_item_id: Optional[int] = Field(None, description="ID of the source item (package_item_id or reporting_effort_item_id)")
    item_type: str = Field(..., description="Type of item: TLF or Dataset")
    item_subtype: str = Field(..., min_length=1, max_length=50, description="Subtype: Table/Listing/Figure for TLF, SDTM/ADaM for Dataset")
    item_code: str = Field(..., min_length=1, max_length=255, description="TLF ID or dataset name")
    is_active: bool = Field(True, description="Whether the item is active")
    
    @field_validator('source_type')
    @classmethod
    def validate_source_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate source_type against enum values."""
        if v is not None:
            valid_values = [member.value for member in SourceType]
            if v not in valid_values:
                raise ValueError(f"source_type must be one of: {', '.join(valid_values)}")
        return v
    
    @field_validator('item_type')
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        """Validate item_type against enum values."""
        valid_values = [member.value for member in ItemType]
        if v not in valid_values:
            raise ValueError(f"item_type must be one of: {', '.join(valid_values)}")
        return v
    
    @field_validator('item_subtype')
    @classmethod
    def validate_subtype(cls, v: str, info) -> str:
        """Validate item_subtype based on item_type."""
        if 'item_type' in info.data:
            item_type = info.data['item_type']
            if item_type == "TLF":
                valid_subtypes = ['Table', 'Listing', 'Figure']
                if v not in valid_subtypes:
                    raise ValueError(f"For TLF items, subtype must be one of: {', '.join(valid_subtypes)}")
            elif item_type == "Dataset":
                valid_subtypes = ['SDTM', 'ADaM']
                if v not in valid_subtypes:
                    raise ValueError(f"For Dataset items, subtype must be one of: {', '.join(valid_subtypes)}")
        return v


class ReportingEffortItemCreate(ReportingEffortItemBase):
    """Schema for creating a ReportingEffortItem."""
    pass


class ReportingEffortItemUpdate(BaseModel):
    """Schema for updating a ReportingEffortItem."""
    
    item_subtype: Optional[str] = Field(None, min_length=1, max_length=50, description="Subtype")
    item_code: Optional[str] = Field(None, min_length=1, max_length=255, description="Item code")
    is_active: Optional[bool] = None


class ReportingEffortItemInDB(ReportingEffortItemBase):
    """Schema for ReportingEffortItem from database."""
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ReportingEffortItem(ReportingEffortItemInDB):
    """Schema for ReportingEffortItem response."""
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# TLF Details schemas
class ReportingEffortTlfDetailsBase(BaseModel):
    """Base schema for TLF details."""
    
    title_id: Optional[int] = Field(None, description="Reference to title text element")
    population_flag_id: Optional[int] = Field(None, description="Reference to population flag text element")
    ich_category_id: Optional[int] = Field(None, description="Reference to ICH category text element")


class ReportingEffortTlfDetailsCreate(ReportingEffortTlfDetailsBase):
    """Schema for creating TLF details."""
    pass


class ReportingEffortTlfDetailsInDB(ReportingEffortTlfDetailsBase):
    """Schema for TLF details in database."""
    
    id: int = Field(..., description="TLF details ID")
    reporting_effort_item_id: int = Field(..., description="Reporting effort item ID")
    
    model_config = ConfigDict(from_attributes=True)


# Dataset Details schemas
class ReportingEffortDatasetDetailsBase(BaseModel):
    """Base schema for dataset details."""
    
    label: Optional[str] = Field(None, max_length=255, description="Dataset label")
    sorting_order: Optional[int] = Field(None, description="Display order")
    acronyms: Optional[str] = Field(None, description="JSON array of acronyms")


class ReportingEffortDatasetDetailsCreate(ReportingEffortDatasetDetailsBase):
    """Schema for creating dataset details."""
    pass


class ReportingEffortDatasetDetailsInDB(ReportingEffortDatasetDetailsBase):
    """Schema for dataset details in database."""
    
    id: int = Field(..., description="Dataset details ID")
    reporting_effort_item_id: int = Field(..., description="Reporting effort item ID")
    
    model_config = ConfigDict(from_attributes=True)


# Footnote and Acronym association schemas
class ReportingEffortItemFootnoteBase(BaseModel):
    """Base schema for footnote association."""
    
    footnote_id: int = Field(..., gt=0, description="Footnote text element ID")
    sequence_number: Optional[int] = Field(None, description="Display order")


class ReportingEffortItemFootnoteCreate(ReportingEffortItemFootnoteBase):
    """Schema for creating footnote association."""
    pass


class ReportingEffortItemAcronymBase(BaseModel):
    """Base schema for acronym association."""
    
    acronym_id: int = Field(..., gt=0, description="Acronym text element ID")


class ReportingEffortItemAcronymCreate(ReportingEffortItemAcronymBase):
    """Schema for creating acronym association."""
    pass


class ReportingEffortItemWithDetails(ReportingEffortItemInDB):
    """Schema for ReportingEffortItem with all related details."""
    
    tlf_details: Optional[ReportingEffortTlfDetailsInDB] = None
    dataset_details: Optional[ReportingEffortDatasetDetailsInDB] = None
    footnotes: List[ReportingEffortItemFootnoteBase] = Field(default_factory=list)
    acronyms: List[ReportingEffortItemAcronymBase] = Field(default_factory=list)
    tracker: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReportingEffortItemCreateWithDetails(ReportingEffortItemBase):
    """Schema for creating a reporting effort item with all details."""
    
    tlf_details: Optional[ReportingEffortTlfDetailsCreate] = None
    dataset_details: Optional[ReportingEffortDatasetDetailsCreate] = None
    footnotes: List[ReportingEffortItemFootnoteCreate] = Field(default_factory=list)
    acronyms: List[ReportingEffortItemAcronymCreate] = Field(default_factory=list)
    
    @field_validator('tlf_details', 'dataset_details')
    @classmethod
    def validate_details(cls, v, info):
        """Ensure only appropriate details are provided based on item_type."""
        if 'item_type' in info.data:
            item_type = info.data['item_type']
            field_name = info.field_name
            
            if field_name == 'tlf_details' and item_type == "Dataset" and v is not None:
                raise ValueError("TLF details cannot be provided for Dataset items")
            elif field_name == 'dataset_details' and item_type == "TLF" and v is not None:
                raise ValueError("Dataset details cannot be provided for TLF items")
        return v


# Copy operation schemas
class CopyFromPackageRequest(BaseModel):
    """Request schema for copying items from a package."""
    package_id: int = Field(..., gt=0, description="ID of the source package")
    item_ids: Optional[List[int]] = Field(None, description="Specific item IDs to copy (None = copy all)")


class CopyFromReportingEffortRequest(BaseModel):
    """Request schema for copying items from another reporting effort."""
    source_reporting_effort_id: int = Field(..., gt=0, description="ID of the source reporting effort")
    item_ids: Optional[List[int]] = Field(None, description="Specific item IDs to copy (None = copy all)")