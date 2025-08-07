"""PackageItemFootnote SQLAlchemy model."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PackageItemFootnote(Base):
    """Junction table for package items and footnotes."""
    
    __tablename__ = "package_item_footnotes"
    
    package_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("package_items.id"),
        primary_key=True
    )
    footnote_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        primary_key=True
    )
    sequence_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Display order for footnotes"
    )
    
    # Relationships
    package_item = relationship("PackageItem", back_populates="footnotes")
    footnote = relationship("TextElement")
    
    def __repr__(self) -> str:
        return f"<PackageItemFootnote(package_item_id={self.package_item_id}, footnote_id={self.footnote_id})>"