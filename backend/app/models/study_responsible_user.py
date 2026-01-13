"""StudyResponsibleUser model for study responsibility assignment."""

from sqlalchemy import Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.study import Study


class StudyResponsibleUser(Base, TimestampMixin):
    """Maps users to studies as responsible users.

    Responsible users have LEAD-equivalent permissions within their assigned studies.
    This replaces the LEAD role in user_study_roles with a more explicit ownership model.

    Features:
    - A study can have multiple responsible users
    - is_primary indicates the main responsible person (for display purposes)
    - Responsible users can manage study members, releases, efforts, etc.
    """

    __tablename__ = "study_responsible_users"

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
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this user is the primary responsible person for the study"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="responsible_studies")
    study: Mapped["Study"] = relationship("Study", back_populates="responsible_users")

    # Ensure one assignment per user per study
    __table_args__ = (
        UniqueConstraint('user_id', 'study_id', name='uq_study_responsible_user'),
    )

    def __repr__(self) -> str:
        return f"<StudyResponsibleUser(user_id={self.user_id}, study_id={self.study_id}, is_primary={self.is_primary})>"
