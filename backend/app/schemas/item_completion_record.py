"""Schemas for ItemCompletionRecord - completion tracking for velocity calculation."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ItemCompletionRecordBase(BaseModel):
    """Base schema for ItemCompletionRecord."""
    tracker_id: Optional[int] = Field(None, description="Reference to original tracker")
    study_id: int = Field(..., description="Study ID")
    item_type: str = Field(..., description="Item type: TLF or Dataset")
    item_subtype: str = Field(..., description="Subtype: Table, Listing, Figure, SDTM, ADaM")
    item_code: str = Field(..., description="The TLF ID or dataset name")
    complexity: int = Field(..., ge=1, le=5, description="Complexity score (1-5)")
    production_programmer_id: Optional[int] = Field(None, description="Programmer who completed it")
    programmer_experience_level: Optional[str] = Field(None, description="Experience level at completion")
    programmer_allocation_percent: Optional[int] = Field(None, description="Allocation % at completion")
    completed_at: datetime = Field(..., description="Completion timestamp")
    iso_week: int = Field(..., ge=1, le=53, description="ISO week number")
    iso_year: int = Field(..., description="ISO year")
    had_sister_study: bool = Field(default=False)
    sister_study_id: Optional[int] = Field(None)


class ItemCompletionRecordCreate(ItemCompletionRecordBase):
    """Schema for creating an ItemCompletionRecord."""
    pass


class ItemCompletionRecordInDB(ItemCompletionRecordBase):
    """Schema for ItemCompletionRecord from database."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemCompletionRecord(ItemCompletionRecordInDB):
    """Schema for ItemCompletionRecord response."""
    pass


# Analytics-focused schemas

class WeeklyVelocity(BaseModel):
    """Weekly velocity data point for a programmer or team."""
    iso_year: int
    iso_week: int
    complexity_points: int = Field(..., description="Total complexity points completed")
    item_count: int = Field(..., description="Number of items completed")
    avg_complexity: float = Field(..., description="Average complexity of completed items")


class ProgrammerVelocity(BaseModel):
    """Velocity statistics for a single programmer."""
    user_id: int
    username: str
    study_id: Optional[int] = None
    study_label: Optional[str] = None
    weeks_analyzed: int
    total_complexity_points: int
    total_items_completed: int
    avg_points_per_week: float
    weekly_data: List[WeeklyVelocity]
    data_points: int = Field(..., description="Number of weeks with data")
    confidence: str = Field(..., description="Confidence level: low, medium, high")


class TeamVelocity(BaseModel):
    """Velocity statistics for a study team."""
    study_id: int
    study_label: str
    weeks_analyzed: int
    total_complexity_points: int
    total_items_completed: int
    avg_points_per_week: float
    weekly_data: List[WeeklyVelocity]
    programmer_breakdown: List[ProgrammerVelocity]


class VelocityByItemType(BaseModel):
    """Velocity breakdown by item subtype."""
    item_subtype: str
    complexity_avg: float
    items_completed: int
    complexity_total: int


class CompletionStats(BaseModel):
    """Summary statistics for completions."""
    study_id: int
    study_label: str
    total_completed: int
    completed_this_week: int
    completed_this_month: int
    avg_complexity: float
    by_item_type: List[VelocityByItemType]

