"""StudyDefaultBiostat model for storing the default biostat reviewer per study."""

from sqlalchemy import Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.study import Study


class StudyDefaultBiostat(Base, TimestampMixin):
    """Maps studies to their default biostat reviewer.

    Each study can have one active default biostat reviewer who will be
    automatically assigned to TLF items when QC completes. The biostat
    reviewer must have the BIOSTAT role for that study.
    """

    __tablename__ = "study_default_biostats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this is the active default biostat for the study"
    )

    # Relationships
    study: Mapped["Study"] = relationship(
        "Study",
        backref="default_biostat_assignment"
    )
    user: Mapped["User"] = relationship(
        "User",
        backref="default_biostat_for_studies"
    )

    # Ensure one active default biostat per study
    __table_args__ = (
        UniqueConstraint('study_id', 'user_id', name='uq_study_default_biostat'),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<StudyDefaultBiostat(study_id={self.study_id}, user_id={self.user_id}, is_active={self.is_active})>"
