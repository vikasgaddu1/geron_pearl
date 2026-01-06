"""UserStudyRole model for study-scoped access control."""

from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.study import Study


class StudyRole(str, Enum):
    """Study-specific roles for access control.
    
    - VIEWER: Read-only access (default for all users)
    - EDITOR: Can modify items they're assigned to
    - LEAD: Full admin capabilities within the study
    """
    VIEWER = "VIEWER"
    EDITOR = "EDITOR"
    LEAD = "LEAD"


class UserStudyRole(Base, TimestampMixin):
    """Maps users to studies with specific roles.
    
    This enables study-scoped permissions where:
    - A user can have different roles in different studies
    - LEAD = admin capabilities within that study only
    - Global ADMIN users bypass this (have LEAD access everywhere)
    """
    
    __tablename__ = "user_study_roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    study_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("studies.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    role: Mapped[StudyRole] = mapped_column(
        SQLEnum(StudyRole),
        nullable=False,
        default=StudyRole.VIEWER,
        doc="User's role within this specific study"
    )
    
    # Relationships
    user = relationship("User", back_populates="study_roles")
    study = relationship("Study", back_populates="user_roles")
    
    # Ensure one role per user per study
    __table_args__ = (
        UniqueConstraint('user_id', 'study_id', name='uq_user_study_role'),
    )
    
    def __repr__(self) -> str:
        return f"<UserStudyRole(user_id={self.user_id}, study_id={self.study_id}, role='{self.role}')>"

