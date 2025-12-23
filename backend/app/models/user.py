from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
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


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    department = Column(String(50), nullable=True)
    
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