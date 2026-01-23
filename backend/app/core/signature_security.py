"""Electronic signature security utilities.

This module provides TOTP-based electronic signature functionality:
- Fernet encryption for TOTP secrets (not stored in plaintext)
- Rate limiting with lockout after failed attempts
- Backup codes for recovery
- Signature hash generation and verification
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import pyotp
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


# =============================================================================
# Configuration Constants
# =============================================================================

MAX_FAILED_ATTEMPTS = settings.signature_max_failed_attempts
LOCKOUT_DURATION_MINUTES = settings.signature_lockout_minutes
TOTP_VALID_WINDOW = 1  # ±30 seconds tolerance (1 TOTP time step)


# =============================================================================
# Encryption Functions
# =============================================================================

def _get_fernet() -> Fernet:
    """
    Get Fernet instance for encryption/decryption.

    The key must be 32 url-safe base64-encoded bytes.
    Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    key = settings.signature_encryption_key
    # If key is the dev default, use a fixed valid Fernet key for development
    # WARNING: Change this key in production!
    if key == "dev-signature-key-change-in-production-32b":
        # Fixed dev key - DO NOT USE IN PRODUCTION
        key = "dGhpcy1pcy1hLWRldi1rZXktZm9yLXRlc3Rpbmc="  # base64 for dev
        # Generate a proper key that's consistent for dev
        import base64
        # Use a fixed 32-byte key for dev (padded to 32 bytes)
        fixed_key = b"pearl-dev-signature-key-32bytes!"  # exactly 32 bytes
        key = base64.urlsafe_b64encode(fixed_key).decode()
    return Fernet(key.encode())


def encrypt_secret(plaintext: str) -> str:
    """
    Encrypt a TOTP secret using Fernet.

    Args:
        plaintext: The TOTP secret to encrypt

    Returns:
        The encrypted secret as a string (base64 encoded)
    """
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """
    Decrypt a TOTP secret.

    Args:
        ciphertext: The encrypted secret

    Returns:
        The decrypted TOTP secret

    Raises:
        InvalidToken: If decryption fails (wrong key or corrupted data)
    """
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


# =============================================================================
# TOTP Functions
# =============================================================================

def generate_signature_secret() -> str:
    """
    Generate a new TOTP secret for electronic signatures.

    Returns:
        A base32-encoded secret string (plaintext - encrypt before storing!)
    """
    return pyotp.random_base32()


def get_signature_uri(email: str, secret: str) -> str:
    """
    Get the provisioning URI for QR code generation.

    Args:
        email: User's email or username for display
        secret: The plaintext TOTP secret

    Returns:
        otpauth:// URI for QR code generation
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(email, issuer_name="PEARL E-Signature")


def verify_totp(secret: str, token: str) -> bool:
    """
    Verify a TOTP token against the secret.

    Args:
        secret: The plaintext TOTP secret
        token: The 6-digit token to verify

    Returns:
        True if valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=TOTP_VALID_WINDOW)


# =============================================================================
# Backup Codes
# =============================================================================

def generate_backup_codes(count: int = 10) -> list[str]:
    """
    Generate one-time backup codes for signature recovery.

    Args:
        count: Number of codes to generate (default 10)

    Returns:
        List of uppercase hex codes (e.g., "A1B2C3D4")
    """
    return [secrets.token_hex(4).upper() for _ in range(count)]


def verify_backup_code(stored_codes: str, provided_code: str) -> tuple[bool, str]:
    """
    Verify a backup code and return the remaining codes.

    Args:
        stored_codes: Comma-separated list of valid codes
        provided_code: The code to verify

    Returns:
        Tuple of (is_valid, remaining_codes_string)
    """
    codes = [c.strip() for c in stored_codes.split(",") if c.strip()]
    provided_upper = provided_code.strip().upper()

    if provided_upper in codes:
        codes.remove(provided_upper)
        return True, ",".join(codes)

    return False, stored_codes


# =============================================================================
# Rate Limiting
# =============================================================================

def is_user_locked_out(locked_until: Optional[datetime]) -> bool:
    """
    Check if user is currently locked out from signing.

    Args:
        locked_until: The lockout expiry timestamp (UTC, timezone-aware)

    Returns:
        True if still locked out, False otherwise
    """
    if locked_until is None:
        return False

    # Handle both timezone-aware and naive datetimes
    now = datetime.now(timezone.utc)
    if locked_until.tzinfo is None:
        # Assume UTC for naive datetimes
        locked_until = locked_until.replace(tzinfo=timezone.utc)

    return now < locked_until


def get_lockout_expiry() -> datetime:
    """
    Get the lockout expiry timestamp for a new lockout.

    Returns:
        UTC datetime when the lockout expires
    """
    return datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)


def get_lockout_remaining_minutes(locked_until: Optional[datetime]) -> int:
    """
    Get remaining lockout time in minutes.

    Args:
        locked_until: The lockout expiry timestamp

    Returns:
        Remaining minutes (0 if not locked out)
    """
    if locked_until is None:
        return 0

    now = datetime.now(timezone.utc)
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)

    if now >= locked_until:
        return 0

    remaining = (locked_until - now).total_seconds() / 60
    return max(1, int(remaining))  # At least 1 minute if still locked


# =============================================================================
# Signature Hash Functions
# =============================================================================

def generate_signature_hash(
    effort_id: int,
    user_id: int,
    timestamp: datetime,
    items_snapshot: str,
) -> str:
    """
    Generate a cryptographic hash for the electronic signature.

    This hash proves the signature is authentic and the data hasn't been
    tampered with. It includes all relevant data at the time of signing.

    Args:
        effort_id: The reporting effort ID
        user_id: The signing user's ID
        timestamp: The signing timestamp (UTC)
        items_snapshot: JSON snapshot of all items at signing time

    Returns:
        Hash string in format "SHA256:hexdigest"
    """
    # Normalize timestamp to ISO format
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    data = f"{effort_id}:{user_id}:{timestamp.isoformat()}:{items_snapshot}"
    hash_value = hashlib.sha256(data.encode()).hexdigest()
    return f"SHA256:{hash_value}"


def verify_signature_hash(
    stored_hash: str,
    effort_id: int,
    user_id: int,
    timestamp: datetime,
    items_snapshot: str,
) -> bool:
    """
    Verify that a signature hash matches the original data.

    Args:
        stored_hash: The stored signature hash to verify
        effort_id: The reporting effort ID
        user_id: The signing user's ID
        timestamp: The signing timestamp
        items_snapshot: The items snapshot from signature history

    Returns:
        True if hash matches, False otherwise
    """
    expected_hash = generate_signature_hash(
        effort_id, user_id, timestamp, items_snapshot
    )
    return stored_hash == expected_hash
