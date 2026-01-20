from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING, List, Optional
from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tracker_comment import TrackerComment
    from app.models.user_study_role import UserStudyRole
    from app.models.study_responsible_user import StudyResponsibleUser
    from app.models.tenant import Tenant


class UserDepartment(str, Enum):
    PROGRAMMING = "programming"
    BIOSTATISTICS = "biostatistics"
    MANAGEMENT = "management"


class AuthProvider(str, Enum):
    """Authentication provider enum."""
    local = "local"
    google = "google"
    microsoft = "microsoft"
    github = "github"
    okta = "okta"
    custom = "custom"


class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    # Composite indexes for multi-tenant queries
    __table_args__ = (
        Index('ix_users_tenant_email', 'tenant_id', 'email'),
        Index('ix_users_tenant_active', 'tenant_id', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenancy: Each user belongs to exactly one tenant
    tenant_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant this user belongs to"
    )
    
    username = Column(String, unique=True, index=True, nullable=False)
    # Note: email uniqueness is now per-tenant (enforced at application level)
    email = Column(String, index=True, nullable=True)  # Required for password reset
    is_admin = Column(Boolean, nullable=False, default=False, doc="Whether user has tenant admin privileges")
    department = Column(String(50), nullable=True)
    
    # Authentication fields
    password_hash = Column(String, nullable=True)  # Nullable for SSO users
    auth_provider = Column(SQLEnum(AuthProvider), nullable=False, default=AuthProvider.local)
    auth_provider_id = Column(String, nullable=True)  # External user ID from SSO
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime, nullable=True)
    
    # Password reset fields
    reset_token = Column(String, nullable=True)  # Hashed reset token
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Comment relationships
    comments = relationship(
        "TrackerComment",
        foreign_keys="TrackerComment.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    resolved_comments = relationship(
        "TrackerComment",
        foreign_keys="TrackerComment.resolved_by_user_id",
        back_populates="resolved_by_user"
    )
    
    # Study-scoped role assignments
    study_roles = relationship(
        "UserStudyRole",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Studies where this user is responsible (replaces LEAD role)
    responsible_studies = relationship(
        "StudyResponsibleUser",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Tenant relationship
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users"
    )