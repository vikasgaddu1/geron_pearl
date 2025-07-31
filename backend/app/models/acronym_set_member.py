"""AcronymSetMember SQLAlchemy model."""

from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.acronym import Acronym
    from app.models.acronym_set import AcronymSet


class AcronymSetMember(Base, TimestampMixin):
    """Junction table for many-to-many relationship between acronym sets and acronyms."""
    
    __tablename__ = "acronym_set_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    acronym_set_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("acronym_sets.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        doc="Foreign key to acronym set"
    )
    acronym_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("acronyms.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        doc="Foreign key to acronym"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False,
        doc="Sort order for consistent presentation"
    )
    
    # Relationships
    acronym_set: Mapped["AcronymSet"] = relationship(
        "AcronymSet", 
        back_populates="acronym_set_members"
    )
    acronym: Mapped["Acronym"] = relationship(
        "Acronym", 
        back_populates="acronym_set_members"
    )
    
    # Unique constraint: each acronym can only be in a set once
    __table_args__ = (
        UniqueConstraint('acronym_set_id', 'acronym_id', name='uq_acronym_set_member'),
    )
    
    def __repr__(self) -> str:
        return f"<AcronymSetMember(id={self.id}, set_id={self.acronym_set_id}, acronym_id={self.acronym_id}, sort_order={self.sort_order})>"