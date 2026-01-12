"""SQLAlchemy model for ErrorLog."""

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ErrorLog(Base):
    """Error log for tracking application errors from frontend and backend."""

    __tablename__ = "error_log"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Error classification
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Error source: BACKEND or FRONTEND"
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Error severity: INFO, WARNING, ERROR, CRITICAL"
    )
    error_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Error type/category (e.g., ValidationError, HTTPException, TypeError)"
    )

    # Error details
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Error message"
    )
    stack_trace: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Full stack trace if available"
    )

    # Request context
    request_method: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        doc="HTTP method (GET, POST, etc.)"
    )
    request_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
        doc="Request path/URL"
    )
    request_body: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Request body (sanitized, no secrets)"
    )
    response_status: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="HTTP response status code"
    )

    # User tracking
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        doc="User who encountered the error (if authenticated)"
    )

    # Client metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address of the client"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User agent string"
    )

    # Frontend-specific fields
    component_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        doc="React component where error occurred (frontend only)"
    )
    browser_info: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Browser/OS information (frontend only)"
    )

    # Correlation
    correlation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        doc="UUID for correlating related errors"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="When the error occurred"
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        backref="error_logs"
    )

    def __repr__(self) -> str:
        return f"<ErrorLog(id={self.id}, source={self.source}, severity={self.severity}, type={self.error_type})>"
