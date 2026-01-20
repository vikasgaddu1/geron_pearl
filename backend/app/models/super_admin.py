"""Super admin model for platform-level administration."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class SuperAdmin(Base, TimestampMixin):
    """
    Super admin model for SaaS platform administrators.
    
    IMPORTANT: This is completely separate from the User model.
    Super admins:
    - Have their own login page (/admin/login)
    - Use a different JWT secret and issuer
    - Can view all tenants' data
    - Can impersonate tenant admins for debugging
    - Require MFA for security
    
    Super admin authentication bypasses RLS by using a BYPASSRLS database role.
    """
    __tablename__ = "super_admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Authentication
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="Super admin email (used for login)"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="Hashed password"
    )
    
    # MFA (Multi-Factor Authentication)
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="TOTP secret for MFA (encrypted)"
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Whether MFA is enabled (required for production)"
    )
    mfa_backup_codes: Mapped[Optional[str]] = mapped_column(
        String(1000), 
        nullable=True,
        doc="Encrypted backup codes for MFA recovery"
    )
    
    # Profile
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="Display name"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True,
        doc="Whether super admin account is active"
    )
    
    # Audit
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        doc="Last login timestamp"
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45), 
        nullable=True,
        doc="Last login IP address"
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Failed login attempts (for lockout)"
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True,
        doc="Account locked until this timestamp"
    )

    def __repr__(self) -> str:
        return f"<SuperAdmin(id={self.id}, email='{self.email}', mfa_enabled={self.mfa_enabled})>"
    
    @property
    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def increment_failed_login(self) -> None:
        """Increment failed login counter and lock if threshold reached."""
        self.failed_login_attempts += 1
        # Lock after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_login(self) -> None:
        """Reset failed login counter on successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None


# Default super admin to create on first setup
DEFAULT_SUPER_ADMIN = {
    "email": "superadmin@pearl.local",
    "name": "Super Admin",
    "mfa_enabled": False,  # Should be enabled in production
}
