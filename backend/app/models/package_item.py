"""PackageItem SQLAlchemy model."""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.models.enums import ItemType


class PackageItem(Base, TimestampMixin):
    """Package item table model for TLFs and Datasets."""
    
    __tablename__ = "package_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id"), nullable=False, index=True)
    item_type: Mapped[ItemType] = mapped_column(
        Enum(ItemType, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
        doc="Type of package item (TLF or Dataset)"
    )
    item_subtype: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Subtype: Table/Listing/Figure for TLF, SDTM/ADaM for Dataset"
    )
    item_code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="The actual TLF ID or dataset name"
    )
    
    # Relationships
    package = relationship("Package", back_populates="package_items")
    tlf_details = relationship("PackageTlfDetails", back_populates="package_item", uselist=False)
    dataset_details = relationship("PackageDatasetDetails", back_populates="package_item", uselist=False)
    footnotes = relationship("PackageItemFootnote", back_populates="package_item")
    acronyms = relationship("PackageItemAcronym", back_populates="package_item")
    
    # Unique constraint: each package can have only one item with same type, subtype, and code
    __table_args__ = (
        UniqueConstraint('package_id', 'item_type', 'item_subtype', 'item_code', 
                        name='uq_package_item_unique'),
    )
    
    def __repr__(self) -> str:
        return f"<PackageItem(id={self.id}, package_id={self.package_id}, type={self.item_type.value}, code='{self.item_code}')>"