"""PackageItemAcronym SQLAlchemy model."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PackageItemAcronym(Base):
    """Junction table for package items and acronyms."""
    
    __tablename__ = "package_item_acronyms"
    
    package_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("package_items.id"),
        primary_key=True
    )
    acronym_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        primary_key=True
    )
    
    # Relationships
    package_item = relationship("PackageItem", back_populates="acronyms")
    acronym = relationship("TextElement")
    
    def __repr__(self) -> str:
        return f"<PackageItemAcronym(package_item_id={self.package_item_id}, acronym_id={self.acronym_id})>"