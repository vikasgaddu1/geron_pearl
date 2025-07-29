"""Study SQLAlchemy model."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Study(Base):
    """Study table model."""
    
    __tablename__ = "studies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_label: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    def __repr__(self) -> str:
        return f"<Study(id={self.id}, study_label='{self.study_label}')>"