"""TextElement SQLAlchemy model."""

from sqlalchemy import String, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.db.base import Base
from app.db.mixins import TimestampMixin


class TextElementType(enum.Enum):
    """Enum for text element types."""
    title = "title"
    footnote = "footnote"
    population_set = "population_set"


class TextElement(Base, TimestampMixin):
    """Text element table model for titles, footnotes, and population sets."""
    
    __tablename__ = "text_elements"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[TextElementType] = mapped_column(
        Enum(TextElementType), 
        nullable=False, 
        index=True,
        doc="Type of text element"
    )
    label: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        doc="Text content for the element"
    )
    
    def __repr__(self) -> str:
        return f"<TextElement(id={self.id}, type={self.type.value}, label='{self.label[:50]}...')>"