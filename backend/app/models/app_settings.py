"""Application Settings SQLAlchemy model."""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class AppSettings(Base, TimestampMixin):
    """Application-wide settings table.

    This table is designed to hold a single row (id=1) with all
    application settings. The single_row constraint ensures only
    one configuration exists.
    """

    __tablename__ = "app_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Settings fields
    default_due_date_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,
        comment="Default number of days to add when auto-setting due dates"
    )

    # Track who last updated settings
    updated_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])

    def __repr__(self) -> str:
        return f"<AppSettings(id={self.id}, default_due_date_offset={self.default_due_date_offset})>"
