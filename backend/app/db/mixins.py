"""Database mixins for reusable model components."""

from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Mixin to add timestamp fields to models."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        doc="Timestamp when the record was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False,
        doc="Timestamp when the record was last updated"
    )