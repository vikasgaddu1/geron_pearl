"""Study SQLAlchemy model."""

from typing import TYPE_CHECKING, List
from sqlalchemy import Column, Integer, String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user_study_role import UserStudyRole
    from app.models.study_responsible_user import StudyResponsibleUser
    from app.models.tenant import Tenant


class Study(Base, TimestampMixin):
    """Study table model."""
    
    __tablename__ = "studies"
    
    # Composite indexes and constraints for multi-tenant queries
    __table_args__ = (
        # study_label must be unique within a tenant
        UniqueConstraint('tenant_id', 'study_label', name='uq_studies_tenant_label'),
        Index('ix_studies_tenant_created', 'tenant_id', 'created_at'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Multi-tenancy: Each study belongs to exactly one tenant
    tenant_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant this study belongs to"
    )
    
    # Note: study_label uniqueness is now per-tenant (via composite unique constraint)
    study_label: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Relationships
    database_releases = relationship("DatabaseRelease", back_populates="study")
    reporting_efforts = relationship("ReportingEffort", back_populates="study")
    
    # User role assignments for this study
    user_roles = relationship(
        "UserStudyRole",
        back_populates="study",
        cascade="all, delete-orphan"
    )

    # Responsible users for this study (replaces LEAD role)
    responsible_users: Mapped[List["StudyResponsibleUser"]] = relationship(
        "StudyResponsibleUser",
        back_populates="study",
        cascade="all, delete-orphan"
    )
    
    # Tenant relationship
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        backref="studies"
    )

    def __repr__(self) -> str:
        return f"<Study(id={self.id}, tenant_id={self.tenant_id}, study_label='{self.study_label}')>"