"""Acronym SQLAlchemy model."""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.acronym_set_member import AcronymSetMember


class Acronym(Base, TimestampMixin):
    """Acronym table model for individual acronym definitions."""
    
    __tablename__ = "acronyms"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        unique=True,
        index=True,
        doc="Acronym key (e.g., 'NA', 'EU')"
    )
    value: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        index=True,
        doc="Acronym definition (e.g., 'North America', 'Europe')"
    )
    description: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        doc="Optional detailed description of the acronym"
    )
    
    # Relationships
    acronym_set_members: Mapped[List["AcronymSetMember"]] = relationship(
        "AcronymSetMember", 
        back_populates="acronym",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Acronym(id={self.id}, key='{self.key}', value='{self.value}')>"