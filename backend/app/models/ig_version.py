"""SQLAlchemy model for Implementation Guide (IG) Versions."""

from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.db.base import Base
from app.db.mixins import TimestampMixin


class StandardType(str, Enum):
    """Standard type enum - SDTM or ADaM."""
    SDTM = "SDTM"
    ADAM = "ADaM"


class IGVersion(Base, TimestampMixin):
    """Implementation Guide Version model for tracking SDTM and ADaM versions."""
    
    __tablename__ = "ig_versions"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Standard type - SDTM or ADaM
    standard_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        doc="Type of standard: SDTM or ADaM"
    )
    
    # Version number (e.g., "3.2", "3.3", "3.4" for SDTM, "1.1", "1.2" for ADaM)
    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Version number (e.g., 3.2, 3.3, 1.1)"
    )
    
    # Optional description
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional description for this version"
    )
    
    # Active flag for soft delete / hide
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this version is available for selection"
    )
    
    # Unique constraint on standard_type + version
    __table_args__ = (
        UniqueConstraint('standard_type', 'version', name='uq_ig_version_standard_version'),
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<IGVersion(id={self.id}, type={self.standard_type}, version='{self.version}')>"






