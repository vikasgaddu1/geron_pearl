"""DatabaseRelease SQLAlchemy model."""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class DatabaseRelease(Base, TimestampMixin):
    """Database release table model."""
    
    __tablename__ = "database_releases"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), nullable=False, index=True)
    database_release_label: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Relationships
    study = relationship("Study", back_populates="database_releases")
    reporting_efforts = relationship("ReportingEffort", back_populates="database_release")
    
    # Unique constraint: each study can have only one database release with the same label
    __table_args__ = (
        UniqueConstraint('study_id', 'database_release_label', name='uq_study_database_release_label'),
    )
    
    def __repr__(self) -> str:
        return f"<DatabaseRelease(id={self.id}, study_id={self.study_id}, database_release_label='{self.database_release_label}')>"