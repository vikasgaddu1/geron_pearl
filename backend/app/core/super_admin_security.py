"""Super Admin authentication and security.

This module provides SEPARATE authentication for super admins:
- Different JWT secret and issuer
- MFA enforcement
- Impersonation tokens with strict controls
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

import pyotp
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings for super admin (SEPARATE from tenant users)
SUPER_ADMIN_JWT_SECRET = settings.super_admin_jwt_secret
SUPER_ADMIN_JWT_ALGORITHM = "HS256"
SUPER_ADMIN_TOKEN_EXPIRE_MINUTES = 60  # Shorter than regular tokens
SUPER_ADMIN_ISSUER = "pearl-superadmin"

# Impersonation settings
IMPERSONATION_TOKEN_EXPIRE_MINUTES = 60  # 1 hour max
IMPERSONATION_ISSUER = "pearl-impersonation"


# Bearer token extractor
super_admin_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_super_admin_token(
    super_admin_id: int,
    email: str,
) -> str:
    """
    Create a JWT token for super admin.
    
    Uses a DIFFERENT secret than tenant user tokens.
    """
    expire = datetime.utcnow() + timedelta(minutes=SUPER_ADMIN_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(super_admin_id),
        "email": email,
        "type": "super_admin",
        "iss": SUPER_ADMIN_ISSUER,
        "exp": expire,
    }
    return jwt.encode(to_encode, SUPER_ADMIN_JWT_SECRET, algorithm=SUPER_ADMIN_JWT_ALGORITHM)


def create_impersonation_token(
    super_admin_id: int,
    tenant_id: int,
    target_user_id: int,
    read_only: bool = True,
) -> str:
    """
    Create an impersonation token for a super admin to view a tenant.
    
    SECURITY FEATURES:
    - 1 hour expiry (non-renewable)
    - Contains super_admin_id for audit trail
    - read_only flag (default True)
    - Different issuer than regular tokens
    """
    expire = datetime.utcnow() + timedelta(minutes=IMPERSONATION_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(target_user_id),  # The user being impersonated
        "tenant_id": tenant_id,
        "type": "impersonation",
        "iss": IMPERSONATION_ISSUER,
        "exp": expire,
        "super_admin_id": super_admin_id,  # Who is impersonating
        "read_only": read_only,
        "impersonation_started_at": datetime.utcnow().isoformat(),
    }
    return jwt.encode(to_encode, SUPER_ADMIN_JWT_SECRET, algorithm=SUPER_ADMIN_JWT_ALGORITHM)


def decode_super_admin_token(token: str) -> dict:
    """
    Decode and validate a super admin token.
    
    Raises JWTError if invalid.
    """
    payload = jwt.decode(
        token,
        SUPER_ADMIN_JWT_SECRET,
        algorithms=[SUPER_ADMIN_JWT_ALGORITHM],
        issuer=SUPER_ADMIN_ISSUER,
    )
    
    if payload.get("type") != "super_admin":
        raise JWTError("Invalid token type")
    
    return payload


def decode_impersonation_token(token: str) -> dict:
    """
    Decode and validate an impersonation token.
    
    Raises JWTError if invalid.
    """
    payload = jwt.decode(
        token,
        SUPER_ADMIN_JWT_SECRET,
        algorithms=[SUPER_ADMIN_JWT_ALGORITHM],
        issuer=IMPERSONATION_ISSUER,
    )
    
    if payload.get("type") != "impersonation":
        raise JWTError("Invalid token type")
    
    return payload


# =============================================================================
# MFA (Multi-Factor Authentication)
# =============================================================================

def generate_mfa_secret() -> str:
    """Generate a new MFA secret for TOTP."""
    return pyotp.random_base32()


def get_mfa_uri(email: str, secret: str) -> str:
    """Get the provisioning URI for MFA setup (for QR code)."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(email, issuer_name="PEARL Super Admin")


def verify_mfa_token(secret: str, token: str) -> bool:
    """Verify a TOTP token against the secret."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # Allow 1 period tolerance


def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate a set of backup codes for MFA recovery."""
    return [secrets.token_hex(4).upper() for _ in range(count)]


# =============================================================================
# FastAPI Dependencies
# =============================================================================

async def get_current_super_admin(
    credentials: HTTPAuthorizationCredentials = Depends(super_admin_bearer),
    db: AsyncSession = Depends(get_db),
) -> SuperAdmin:
    """
    Dependency to get the current authenticated super admin.
    
    Raises 401 if not authenticated or token invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = decode_super_admin_token(credentials.credentials)
        super_admin_id = int(payload["sub"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(SuperAdmin).where(SuperAdmin.id == super_admin_id)
    )
    super_admin = result.scalar_one_or_none()
    
    if not super_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Super admin not found",
        )
    
    if not super_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin account is deactivated",
        )
    
    return super_admin


async def require_mfa(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
) -> SuperAdmin:
    """
    Dependency that requires MFA to be enabled.
    
    For production security, super admins must have MFA enabled.
    """
    if settings.environment == "production" and not super_admin.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA must be enabled for super admin access in production",
        )
    return super_admin


# =============================================================================
# Impersonation Audit
# =============================================================================

async def log_impersonation_start(
    db: AsyncSession,
    super_admin: SuperAdmin,
    tenant: Tenant,
    target_user_id: int,
    ip_address: Optional[str] = None,
) -> None:
    """Log the start of an impersonation session to the audit trail."""
    from app.crud.audit_log import audit_log
    
    await audit_log.log_action(
        db,
        table_name="impersonation",
        record_id=tenant.id,
        action="IMPERSONATION_START",
        user_id=None,  # Super admin, not a regular user
        changes={
            "super_admin_id": super_admin.id,
            "super_admin_email": super_admin.email,
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "target_user_id": target_user_id,
        },
        ip_address=ip_address,
    )


async def log_impersonation_end(
    db: AsyncSession,
    super_admin_id: int,
    tenant_id: int,
    ip_address: Optional[str] = None,
) -> None:
    """Log the end of an impersonation session."""
    from app.crud.audit_log import audit_log
    
    await audit_log.log_action(
        db,
        table_name="impersonation",
        record_id=tenant_id,
        action="IMPERSONATION_END",
        user_id=None,
        changes={
            "super_admin_id": super_admin_id,
            "tenant_id": tenant_id,
        },
        ip_address=ip_address,
    )
