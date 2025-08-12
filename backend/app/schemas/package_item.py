"""PackageItem Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ItemTypeEnum(str, Enum):
    """Package item type enum."""
    TLF = "TLF"
    Dataset = "Dataset"


class PackageItemBase(BaseModel):
    """Base PackageItem schema with common fields."""
    
    package_id: int = Field(..., gt=0, description="Package ID")
    item_type: ItemTypeEnum = Field(..., description="Item type: TLF or Dataset")
    item_subtype: str = Field(..., min_length=1, max_length=50, description="Subtype: Table/Listing/Figure or SDTM/ADaM")
    item_code: str = Field(..., min_length=1, max_length=255, description="TLF ID or dataset name")
    
    @field_validator('item_subtype')
    @classmethod
    def validate_subtype(cls, v: str, info) -> str:
        """Validate item_subtype based on item_type."""
        if 'item_type' in info.data:
            item_type = info.data['item_type']
            if item_type == ItemTypeEnum.TLF:
                valid_subtypes = ['Table', 'Listing', 'Figure']
                if v not in valid_subtypes:
                    raise ValueError(f"For TLF items, subtype must be one of: {', '.join(valid_subtypes)}")
            elif item_type == ItemTypeEnum.Dataset:
                valid_subtypes = ['SDTM', 'ADaM']
                if v not in valid_subtypes:
                    raise ValueError(f"For Dataset items, subtype must be one of: {', '.join(valid_subtypes)}")
        return v


class PackageItemCreate(PackageItemBase):
    """Schema for creating a new package item."""
    
    pass


class PackageItemUpdate(BaseModel):
    """Schema for updating an existing package item."""
    
    item_subtype: Optional[str] = Field(None, min_length=1, max_length=50, description="Subtype")
    item_code: Optional[str] = Field(None, min_length=1, max_length=255, description="Item code")


# TLF Details schemas
class PackageTlfDetailsBase(BaseModel):
    """Base schema for TLF details."""
    
    title_id: Optional[int] = Field(None, description="Reference to title text element")
    population_flag_id: Optional[int] = Field(None, description="Reference to population flag text element")
    ich_category_id: Optional[int] = Field(None, description="Reference to ICH category text element")


class PackageTlfDetailsCreate(PackageTlfDetailsBase):
    """Schema for creating TLF details."""
    
    pass


class PackageTlfDetailsInDB(PackageTlfDetailsBase):
    """Schema for TLF details in database."""
    
    id: int = Field(..., description="TLF details ID")
    package_item_id: int = Field(..., description="Package item ID")
    
    model_config = ConfigDict(from_attributes=True)


# Dataset Details schemas
class PackageDatasetDetailsBase(BaseModel):
    """Base schema for dataset details."""
    
    label: Optional[str] = Field(None, max_length=255, description="Dataset label")
    sorting_order: Optional[int] = Field(None, description="Display order")
    acronyms: Optional[str] = Field(None, description="JSON array of acronyms")


class PackageDatasetDetailsCreate(PackageDatasetDetailsBase):
    """Schema for creating dataset details."""
    
    pass


class PackageDatasetDetailsInDB(PackageDatasetDetailsBase):
    """Schema for dataset details in database."""
    
    id: int = Field(..., description="Dataset details ID")
    package_item_id: int = Field(..., description="Package item ID")
    
    model_config = ConfigDict(from_attributes=True)


# Footnote and Acronym association schemas
class PackageItemFootnoteBase(BaseModel):
    """Base schema for footnote association."""
    
    footnote_id: int = Field(..., gt=0, description="Footnote text element ID")
    sequence_number: Optional[int] = Field(None, description="Display order")


class PackageItemFootnoteCreate(PackageItemFootnoteBase):
    """Schema for creating footnote association."""
    
    pass


class PackageItemAcronymBase(BaseModel):
    """Base schema for acronym association."""
    
    acronym_id: int = Field(..., gt=0, description="Acronym text element ID")


class PackageItemAcronymCreate(PackageItemAcronymBase):
    """Schema for creating acronym association."""
    
    pass


# Complete PackageItem schemas
class PackageItemInDB(PackageItemBase):
    """Schema representing a package item as stored in database."""
    
    id: int = Field(..., description="Package item ID")
    created_at: datetime = Field(..., description="Timestamp when the item was created")
    updated_at: datetime = Field(..., description="Timestamp when the item was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class PackageItem(PackageItemInDB):
    """Schema for package item responses."""
    
    tlf_details: Optional[PackageTlfDetailsInDB] = None
    dataset_details: Optional[PackageDatasetDetailsInDB] = None
    footnotes: List[PackageItemFootnoteBase] = Field(default_factory=list)
    acronyms: List[PackageItemAcronymBase] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class PackageItemCreateWithDetails(PackageItemBase):
    """Schema for creating a package item with all details."""
    
    tlf_details: Optional[PackageTlfDetailsCreate] = None
    dataset_details: Optional[PackageDatasetDetailsCreate] = None
    footnotes: List[PackageItemFootnoteCreate] = Field(default_factory=list)
    acronyms: List[PackageItemAcronymCreate] = Field(default_factory=list)
    
    @field_validator('tlf_details', 'dataset_details')
    @classmethod
    def validate_details(cls, v, info):
        """Ensure only appropriate details are provided based on item_type."""
        if 'item_type' in info.data:
            item_type = info.data['item_type']
            field_name = info.field_name
            
            if field_name == 'tlf_details' and item_type == ItemTypeEnum.Dataset and v is not None:
                raise ValueError("TLF details cannot be provided for Dataset items")
            elif field_name == 'dataset_details' and item_type == ItemTypeEnum.TLF and v is not None:
                raise ValueError("Dataset details cannot be provided for TLF items")
        return v