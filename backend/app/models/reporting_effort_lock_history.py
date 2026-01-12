"""SQLAlchemy model for ReportingEffortLockHistory."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LockAction

if TYPE_CHECKING:
    from app.models.reporting_effort import ReportingEffort
    from app.models.user import User


class ReportingEffortLockHistory(Base):
    """History of lock/unlock actions on reporting efforts."""

    __tablename__ = "reporting_effort_lock_history"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    reporting_effort_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reporting_efforts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The reporting effort that was locked/unlocked"
    )
    performed_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        doc="User who performed the lock/unlock action"
    )

    # Action details
    action: Mapped[LockAction] = mapped_column(
        Enum(LockAction),
        nullable=False,
        doc="The action performed: LOCK or UNLOCK"
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Required reason for the lock/unlock action"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="When the action was performed"
    )

    # Relationships
    reporting_effort: Mapped["ReportingEffort"] = relationship(
        "ReportingEffort",
        backref="lock_history"
    )
    performed_by: Mapped["User"] = relationship(
        "User",
        backref="lock_actions"
    )

    def __repr__(self) -> str:
        return f"<ReportingEffortLockHistory(id={self.id}, effort={self.reporting_effort_id}, action={self.action.value}, by={self.performed_by_id})>"
