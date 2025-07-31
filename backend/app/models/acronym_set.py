"""AcronymSet SQLAlchemy model."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.acronym_set_member import AcronymSetMember


class AcronymSet(Base, TimestampMixin):
    """Acronym set table model for grouping related acronyms."""
    
    __tablename__ = "acronym_sets"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        unique=True,
        index=True,
        doc="Name of the acronym set (e.g., 'Geographic Regions')"
    )
    description: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        doc="Optional description of the acronym set"
    )
    
    # Relationships
    acronym_set_members: Mapped[List["AcronymSetMember"]] = relationship(
        "AcronymSetMember", 
        back_populates="acronym_set",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<AcronymSet(id={self.id}, name='{self.name}')>"