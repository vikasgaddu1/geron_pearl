from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, Boolean, DateTime
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING, List
from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.tracker_comment import TrackerComment


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


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

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)  # Required for password reset
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
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