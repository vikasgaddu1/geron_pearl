"""TextElement SQLAlchemy model."""

from typing import TYPE_CHECKING
from sqlalchemy import String, Enum, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class TextElementType(enum.Enum):
    """Enum for text element types."""
    title = "title"
    footnote = "footnote"
    population_set = "population_set"
    acronyms_set = "acronyms_set"
    ich_category = "ich_category"


class TextElement(Base, TimestampMixin):
    """Text element table model for titles, footnotes, population sets, and acronym sets."""
    
    __tablename__ = "text_elements"
    
    # Composite indexes for multi-tenant queries
    __table_args__ = (
        Index('ix_text_elements_tenant_type', 'tenant_id', 'type'),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Multi-tenancy: Each text element belongs to exactly one tenant
    tenant_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant this text element belongs to"
    )
    
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
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Display content for the element (user-facing text)"
    )
    
    # Tenant relationship
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        backref="text_elements"
    )
    
    # Relationships - These are for reference and won't be used directly
    # package_item_footnotes = relationship("PackageItemFootnote", back_populates="footnote")
    # package_item_acronyms = relationship("PackageItemAcronym", back_populates="acronym")
    
    def __repr__(self) -> str:
        label_preview = self.label[:50] if self.label else ''
        return f"<TextElement(id={self.id}, tenant_id={self.tenant_id}, type={self.type.value}, label='{label_preview}...')>"