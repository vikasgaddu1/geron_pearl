"""TextElement Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.text_element import TextElementType


class TextElementBase(BaseModel):
    """Base TextElement schema with common fields."""
    
    type: TextElementType = Field(..., description="Type of text element (title, footnote, population_set)")
    label: str = Field(..., min_length=1, description="Text content for the element")


class TextElementCreate(TextElementBase):
    """Schema for creating a new text element."""
    
    pass


class TextElementUpdate(BaseModel):
    """Schema for updating an existing text element."""
    
    type: Optional[TextElementType] = Field(None, description="Type of text element")
    label: Optional[str] = Field(None, min_length=1, description="Text content for the element")


class TextElementInDB(TextElementBase):
    """Schema representing a text element as stored in database."""
    
    id: int = Field(..., description="Text element ID")
    created_at: datetime = Field(..., description="Timestamp when the text element was created")
    updated_at: datetime = Field(..., description="Timestamp when the text element was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class TextElement(TextElementInDB):
    """Schema for text element responses."""
    
    pass