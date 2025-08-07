"""PackageDatasetDetails SQLAlchemy model."""

from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PackageDatasetDetails(Base):
    """Dataset-specific details for package items."""
    
    __tablename__ = "package_dataset_details"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("package_items.id"),
        nullable=False,
        unique=True,
        index=True
    )
    label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Dataset label or description"
    )
    sorting_order: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Display/sorting order for the dataset"
    )
    acronyms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of acronyms specific to this dataset"
    )
    
    # Relationships
    package_item = relationship("PackageItem", back_populates="dataset_details")
    
    def __repr__(self) -> str:
        return f"<PackageDatasetDetails(id={self.id}, package_item_id={self.package_item_id}, label='{self.label}')>"