"""PackageTlfDetails SQLAlchemy model."""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PackageTlfDetails(Base):
    """TLF-specific details for package items."""
    
    __tablename__ = "package_tlf_details"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_item_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("package_items.id"), 
        nullable=False, 
        unique=True,
        index=True
    )
    title_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        nullable=True,
        doc="Reference to title text element"
    )
    population_flag_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("text_elements.id"),
        nullable=True,
        doc="Reference to population flag text element"
    )
    
    # Relationships
    package_item = relationship("PackageItem", back_populates="tlf_details")
    title = relationship("TextElement", foreign_keys=[title_id])
    population_flag = relationship("TextElement", foreign_keys=[population_flag_id])
    
    def __repr__(self) -> str:
        return f"<PackageTlfDetails(id={self.id}, package_item_id={self.package_item_id})>"