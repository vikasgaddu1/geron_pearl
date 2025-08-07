"""Package SQLAlchemy model."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Package(Base, TimestampMixin):
    """Package table model."""
    
    __tablename__ = "packages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Relationships
    package_items = relationship("PackageItem", back_populates="package")
    
    def __repr__(self) -> str:
        return f"<Package(id={self.id}, package_name='{self.package_name}')>"