"""Study SQLAlchemy model."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Study(Base, TimestampMixin):
    """Study table model."""
    
    __tablename__ = "studies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_label: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Relationships
    database_releases = relationship("DatabaseRelease", back_populates="study")
    reporting_efforts = relationship("ReportingEffort", back_populates="study")
    package_items = relationship("PackageItem", back_populates="study")
    
    def __repr__(self) -> str:
        return f"<Study(id={self.id}, study_label='{self.study_label}')>"