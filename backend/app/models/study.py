"""Study SQLAlchemy model."""

from typing import TYPE_CHECKING, List
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user_study_role import UserStudyRole


class Study(Base, TimestampMixin):
    """Study table model."""
    
    __tablename__ = "studies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_label: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    # Relationships
    database_releases = relationship("DatabaseRelease", back_populates="study")
    reporting_efforts = relationship("ReportingEffort", back_populates="study")
    
    # User role assignments for this study
    user_roles = relationship(
        "UserStudyRole",
        back_populates="study",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Study(id={self.id}, study_label='{self.study_label}')>"