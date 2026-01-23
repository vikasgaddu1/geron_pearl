# TOTP-Based Electronic Signature Feature for Reporting Efforts

## Overview

Add a TOTP-based electronic signature feature that allows authorized users to permanently sign a Reporting Effort once ALL items are in production. This provides regulatory-grade sign-off with authenticator app verification.

### Key Differences from Existing Lock Feature
| Aspect | Lock | Signature |
|--------|------|-----------|
| Reversibility | Can be unlocked | **Permanent** (cannot unlock signed REs) |
| Pre-condition | None | ALL items must be `in_production_flag=True` |
| Authentication | User password | TOTP 6-digit code |
| Purpose | Temporary freeze | Final sign-off |

### Design Decisions
- **Who can sign**: Users with `is_admin=True` OR users with `LEAD` role for the study (via `study_responsible_users` table)
- **Void/invalidate**: No void option - signatures are permanent for strict compliance
- **Signature count**: Single signature required (not dual)
- **Recovery**: Backup codes provided during setup (like super admin MFA)

---

## Database Changes

### 1. User Model - Add signature TOTP fields
**File**: [backend/app/models/user.py](../backend/app/models/user.py)
```python
# Signature TOTP fields - secrets are ENCRYPTED using Fernet
signature_secret_encrypted: Mapped[Optional[str]] = mapped_column(
    Text, nullable=True, doc="Fernet-encrypted TOTP secret"
)
signature_backup_codes_encrypted: Mapped[Optional[str]] = mapped_column(
    Text, nullable=True, doc="Fernet-encrypted backup codes (comma-separated)"
)
signature_setup_completed: Mapped[bool] = mapped_column(
    Boolean, default=False, nullable=False
)
signature_failed_attempts: Mapped[int] = mapped_column(
    Integer, default=0, nullable=False, doc="Failed TOTP attempts for rate limiting"
)
signature_locked_until: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True, doc="Lockout expiry after failed attempts"
)
```

### 2. ReportingEffort Model - Add signature fields
**File**: [backend/app/models/reporting_effort.py](../backend/app/models/reporting_effort.py)
```python
# Signature fields (permanent, unlike lock which can be reversed)
is_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
signed_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime(timezone=True), nullable=True, doc="UTC timestamp, server-authoritative"
)
signed_by_id: Mapped[Optional[int]] = mapped_column(
    Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
)
signature_hash: Mapped[Optional[str]] = mapped_column(
    String(512), nullable=True, doc="SHA256:hex_hash for verification"
)
signature_reason: Mapped[Optional[str]] = mapped_column(
    Text, nullable=True, doc="Required reason/intent for signing"
)

# Relationships
signed_by: Mapped[Optional["User"]] = relationship(
    "User", foreign_keys=[signed_by_id], backref="signed_reporting_efforts"
)
signature_history: Mapped[List["ReportingEffortSignatureHistory"]] = relationship(
    "ReportingEffortSignatureHistory", back_populates="reporting_effort",
    cascade="all, delete-orphan", order_by="desc(ReportingEffortSignatureHistory.created_at)"
)
```

### 3. New Model: ReportingEffortSignatureHistory
**File**: `backend/app/models/reporting_effort_signature_history.py` (new)
```python
class ReportingEffortSignatureHistory(Base):
    """Immutable audit trail for signature events."""
    __tablename__ = "reporting_effort_signature_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporting_effort_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reporting_efforts.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    signed_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    signed_by_username: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="Preserved username at signing time"
    )
    signature_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    items_snapshot: Mapped[str] = mapped_column(
        Text, nullable=False, doc="JSON snapshot of all items at signing time"
    )
    items_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    reporting_effort: Mapped["ReportingEffort"] = relationship(
        "ReportingEffort", back_populates="signature_history"
    )
    signed_by: Mapped[Optional["User"]] = relationship("User")
```

### 4. Migration
**File**: `backend/migrations/versions/add_electronic_signature.py` (new)

---

## Backend Implementation

### 1. Signature Security Module
**File**: `backend/app/core/signature_security.py` (new)

```python
"""Electronic signature security utilities with encryption and rate limiting."""
from cryptography.fernet import Fernet
from datetime import datetime, timezone, timedelta
import hashlib
import pyotp
import secrets

# Rate limiting constants
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
TOTP_VALID_WINDOW = 1  # ±30 seconds tolerance

def get_encryption_key() -> bytes:
    """Get Fernet key from settings (must be 32 url-safe base64-encoded bytes)."""
    from app.core.config import settings
    return settings.SIGNATURE_ENCRYPTION_KEY.encode()

def encrypt_secret(plaintext: str) -> str:
    """Encrypt TOTP secret using Fernet."""
    f = Fernet(get_encryption_key())
    return f.encrypt(plaintext.encode()).decode()

def decrypt_secret(ciphertext: str) -> str:
    """Decrypt TOTP secret."""
    f = Fernet(get_encryption_key())
    return f.decrypt(ciphertext.encode()).decode()

def generate_signature_secret() -> str:
    """Generate a new TOTP secret (plaintext, encrypt before storing)."""
    return pyotp.random_base32()

def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate one-time backup codes."""
    return [secrets.token_hex(4).upper() for _ in range(count)]

def get_signature_uri(email: str, secret: str) -> str:
    """Get provisioning URI for QR code."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(email, issuer_name="PEARL E-Signature")

def verify_totp(secret: str, token: str) -> bool:
    """Verify TOTP with ±1 time step tolerance (±30 seconds)."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=TOTP_VALID_WINDOW)

def generate_signature_hash(
    effort_id: int, user_id: int, timestamp: datetime, items_snapshot: str
) -> str:
    """Generate SHA-256 hash for signature verification."""
    data = f"{effort_id}:{user_id}:{timestamp.isoformat()}:{items_snapshot}"
    return f"SHA256:{hashlib.sha256(data.encode()).hexdigest()}"

def verify_signature_hash(
    stored_hash: str, effort_id: int, user_id: int,
    timestamp: datetime, items_snapshot: str
) -> bool:
    """Verify signature hash matches original data."""
    expected = generate_signature_hash(effort_id, user_id, timestamp, items_snapshot)
    return stored_hash == expected

def is_user_locked_out(locked_until: datetime | None) -> bool:
    """Check if user is currently locked out from signing."""
    if locked_until is None:
        return False
    return datetime.now(timezone.utc) < locked_until

def get_lockout_expiry() -> datetime:
    """Get lockout expiry timestamp."""
    return datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
```

### 2. CRUD Updates

**User CRUD** - [backend/app/crud/user.py](../backend/app/crud/user.py)
```python
async def setup_signature_totp(self, db: AsyncSession, *, user_id: int) -> tuple[str, list[str]]:
    """Generate TOTP secret and backup codes, store encrypted."""
    from app.core.signature_security import (
        generate_signature_secret, generate_backup_codes, encrypt_secret
    )
    secret = generate_signature_secret()
    backup_codes = generate_backup_codes(10)

    user = await self.get(db, id=user_id)
    user.signature_secret_encrypted = encrypt_secret(secret)
    user.signature_backup_codes_encrypted = encrypt_secret(",".join(backup_codes))
    user.signature_setup_completed = False
    user.signature_failed_attempts = 0
    user.signature_locked_until = None
    await db.commit()

    return secret, backup_codes  # Return plaintext for QR display only

async def complete_signature_setup(self, db: AsyncSession, *, user_id: int, token: str) -> bool:
    """Verify TOTP and mark setup complete."""
    # ... verify and set signature_setup_completed = True

async def verify_signature_token(self, db: AsyncSession, *, user_id: int, token: str) -> tuple[bool, str]:
    """Verify TOTP with rate limiting. Returns (success, error_message)."""
    from app.core.signature_security import (
        decrypt_secret, verify_totp, is_user_locked_out,
        get_lockout_expiry, MAX_FAILED_ATTEMPTS
    )
    user = await self.get(db, id=user_id)

    # Check lockout
    if is_user_locked_out(user.signature_locked_until):
        remaining = (user.signature_locked_until - datetime.now(timezone.utc)).seconds // 60
        return False, f"Account locked. Try again in {remaining} minutes."

    # Verify token
    secret = decrypt_secret(user.signature_secret_encrypted)
    if verify_totp(secret, token):
        user.signature_failed_attempts = 0
        user.signature_locked_until = None
        await db.commit()
        return True, ""

    # Handle failed attempt
    user.signature_failed_attempts += 1
    if user.signature_failed_attempts >= MAX_FAILED_ATTEMPTS:
        user.signature_locked_until = get_lockout_expiry()
    await db.commit()

    remaining = MAX_FAILED_ATTEMPTS - user.signature_failed_attempts
    return False, f"Invalid code. {remaining} attempts remaining."

async def use_backup_code(self, db: AsyncSession, *, user_id: int, code: str) -> bool:
    """Use a one-time backup code (removes it after use)."""
    # ... decrypt, check, remove used code, re-encrypt

async def reset_signature_totp(self, db: AsyncSession, *, user_id: int) -> None:
    """Reset/revoke signature TOTP (admin action or self-service)."""
    user = await self.get(db, id=user_id)
    user.signature_secret_encrypted = None
    user.signature_backup_codes_encrypted = None
    user.signature_setup_completed = False
    user.signature_failed_attempts = 0
    user.signature_locked_until = None
    await db.commit()
```

**Tracker CRUD** - [backend/app/crud/reporting_effort_item_tracker.py](../backend/app/crud/reporting_effort_item_tracker.py)
```python
async def are_all_items_in_production(
    self, db: AsyncSession, *, reporting_effort_id: int
) -> tuple[bool, int, int]:
    """Check if ALL items have in_production_flag=True.
    Returns: (all_in_production, total_items, items_in_production)
    """

async def get_items_snapshot(
    self, db: AsyncSession, *, reporting_effort_id: int
) -> str:
    """Get deterministic JSON snapshot of all items for hash generation.
    Sorted by item ID for consistency.
    """
```

**ReportingEffort CRUD** - [backend/app/crud/reporting_effort.py](../backend/app/crud/reporting_effort.py)
```python
async def sign(
    self, db: AsyncSession, *, id: int, user_id: int, username: str,
    reason: str, items_snapshot: str, items_count: int,
    ip_address: str | None, user_agent: str | None
) -> ReportingEffort:
    """Sign a reporting effort. This is PERMANENT."""
    # 1. Verify not already signed
    # 2. Generate timestamp and hash
    # 3. Update RE: is_signed=True, signed_at, signed_by_id, signature_hash, signature_reason
    # 4. Auto-lock: is_locked=True, locked_at, locked_by_id, lock_reason="Signed electronically"
    # 5. Create ReportingEffortSignatureHistory entry
    # 6. Commit and return

async def get_signature_history(self, db: AsyncSession, *, id: int) -> list:
    """Get signature history entries."""
```

### 3. API Endpoints

**User Signature Setup** - [backend/app/api/v1/users.py](../backend/app/api/v1/users.py)
| Endpoint | Description |
|----------|-------------|
| `POST /users/me/signature/setup` | Start TOTP setup, returns QR URI + backup codes |
| `POST /users/me/signature/verify-setup` | Verify code, complete setup |
| `GET /users/me/signature/status` | Check setup status and lockout state |
| `POST /users/me/signature/reset` | Revoke/regenerate TOTP secret |
| `POST /users/me/signature/use-backup-code` | Use one-time backup code |

**Reporting Effort Signature** - [backend/app/api/v1/reporting_efforts.py](../backend/app/api/v1/reporting_efforts.py)
| Endpoint | Description |
|----------|-------------|
| `GET /{id}/signature-readiness` | Check preconditions (items in prod, user auth setup, not locked out) |
| `POST /{id}/sign` | Sign with TOTP verification |
| `GET /{id}/signature-history` | Get signature audit trail |
| `GET /{id}/verify-signature` | **NEW**: Cryptographically verify signature hash against items |

**Unlock Endpoint Update** - Add check to prevent unlocking signed REs:
```python
@router.post("/{reporting_effort_id}/unlock")
async def unlock_reporting_effort(...):
    # ADD THIS CHECK
    if db_effort.is_signed:
        raise HTTPException(
            status_code=400,
            detail="Cannot unlock: This reporting effort has been signed and is permanently locked."
        )
    # ... existing unlock logic
```

### 4. Schema Updates
**File**: [backend/app/schemas/reporting_effort.py](../backend/app/schemas/reporting_effort.py)
```python
class ReportingEffortSignRequest(BaseModel):
    """Request to sign a reporting effort."""
    totp_token: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    reason: str = Field(..., min_length=10, max_length=1000,
        description="Required reason/intent for signing")

class SignatureVerificationResponse(BaseModel):
    """Response from signature verification."""
    is_valid: bool
    signed_at: datetime | None
    signed_by_username: str | None
    items_match: bool
    items_at_signing: int
    items_current: int
```

### 5. Deletion Protection
**Add checks to prevent deletion of signed entities:**

```python
# In studies.py DELETE endpoint:
if any(re.is_signed for re in study.reporting_efforts):
    raise HTTPException(400, "Cannot delete study with signed reporting efforts")

# In reporting_efforts.py DELETE endpoint:
if db_effort.is_signed:
    raise HTTPException(400, "Cannot delete signed reporting effort")

# In users.py DELETE endpoint:
# Use ondelete="SET NULL" for signed_by_id FK - preserves signature with username in history
```

### 6. WebSocket Broadcasting
Add to [backend/app/api/v1/reporting_efforts.py](../backend/app/api/v1/reporting_efforts.py):
```python
# After successful signing:
await manager.broadcast({
    "type": "reporting_effort_signed",
    "data": serialize_reporting_effort(signed_effort)
})
```

---

## Frontend Implementation

### 1. Install QR Library
```bash
npm install qrcode.react
```

### 2. Type Updates
**File**: [react-frontend/src/types/index.ts](../react-frontend/src/types/index.ts)
```typescript
export interface SignatureReadiness {
  can_sign: boolean
  is_signed: boolean
  has_totp_setup: boolean
  is_responsible: boolean  // Admin OR study LEAD
  all_items_in_production: boolean
  total_items: number
  items_in_production: number
  is_locked_out: boolean
  lockout_remaining_minutes?: number
  blockers: string[]
  signed_by_username?: string
  signed_at?: string
}

export interface SignatureSetupResponse {
  provisioning_uri: string
  backup_codes: string[]  // Show once, user must save
}

export interface SignatureVerification {
  is_valid: boolean
  signed_at?: string
  signed_by_username?: string
  items_match: boolean
  items_at_signing: number
  items_current: number
}
```

### 3. API Endpoints
**File**: [react-frontend/src/api/endpoints/users.ts](../react-frontend/src/api/endpoints/users.ts)
- `setupSignature()` - Returns QR URI + backup codes
- `verifySignatureSetup(token)` - Complete setup
- `getSignatureStatus()` - Check status
- `resetSignature()` - Revoke and start over
- `useBackupCode(code)` - Use backup code

**File**: [react-frontend/src/api/endpoints/reporting-efforts.ts](../react-frontend/src/api/endpoints/reporting-efforts.ts)
- `checkSignatureReadiness(id)` - Pre-sign checks
- `sign(id, token, reason)` - Sign with TOTP
- `getSignatureHistory(id)` - Audit trail
- `verifySignature(id)` - Verify hash integrity

### 4. New Components

**SignatureSetupDialog** - `react-frontend/src/features/settings/SignatureSetupDialog.tsx` (new)
- Step 1: Show QR code using `qrcode.react`
- Step 2: Show backup codes with "I have saved these" confirmation
- Step 3: Verify with 6-digit code
- Error handling for wrong codes with attempt counter

**SignReportingEffortDialog** - `react-frontend/src/features/study-management/SignReportingEffortDialog.tsx` (new)
- Precondition checklist with setup prompt if TOTP not configured
- Reason textarea (required, min 10 chars)
- TOTP code input with lockout warning
- Permanent action warning with confirmation checkbox
- Error feedback for: wrong code, lockout, items not in prod

### 5. UI Integration
- Add "Sign" button to RE cards (disabled if preconditions not met)
- Show signature badge with icon when signed (signer name, date on hover)
- Add signature status filter to RE list view
- Add "Signature Authentication" section to Settings page
- Use `authStore.isResponsibleForStudy(studyId)` for authorization checks

---

## Workflow

### User Setup (One-time)
1. User navigates to Settings > Signature Authentication
2. Clicks "Setup Signature Authentication"
3. Scans QR code with authenticator app
4. **MUST save backup codes** (shown once, 10 codes)
5. Enters 6-digit code to verify
6. Setup complete

### Signing a Reporting Effort
1. All items must have `in_production_flag = true`
2. User must be admin OR have LEAD role for the study
3. User clicks "Sign" button
4. System shows precondition checklist
5. User enters reason (required, min 10 chars)
6. User enters 6-digit TOTP code
7. User confirms permanent action checkbox
8. System verifies TOTP (rate limited: 5 attempts, 15-min lockout)
9. System creates signature hash, auto-locks RE
10. WebSocket broadcasts `reporting_effort_signed`
11. RE is now permanently read-only

### Recovery (Lost Authenticator)
1. User goes to Settings > Signature Authentication
2. Clicks "Use Backup Code"
3. Enters one of the 10 backup codes
4. Can then click "Reset" to set up new TOTP
5. New QR code and backup codes generated

---

## Security Considerations

1. **Encrypted Storage** - TOTP secrets encrypted with Fernet (not plaintext)
2. **Rate Limiting** - 5 failed attempts = 15-minute lockout
3. **Backup Codes** - 10 one-time codes for recovery
4. **SHA-256 Hash** - Includes effort_id, user_id, UTC timestamp, items_snapshot
5. **Items Snapshot** - Captures exact state for verification
6. **Audit Trail** - IP address, user agent, preserved username
7. **Authorization** - Only `is_admin=True` OR study LEAD can sign
8. **No Void** - Signatures permanent, unlock prevented after signing
9. **Deletion Protection** - Cannot delete studies/REs/items with signatures
10. **Clock Tolerance** - ±30 seconds (1 TOTP time step)

---

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Items change between readiness check and sign | Optimistic concurrency: re-check at sign time |
| RE already locked by someone else | Allow signing (signature takes precedence) |
| User signs then is deactivated | Signature preserved via SET NULL FK + username in history |
| Study deletion with signed RE | Blocked with error message |
| TOTP clock drift | ±30 second tolerance (valid_window=1) |
| Concurrent sign attempts | First to commit wins, second gets "already signed" error |
| User locked out | Show remaining lockout time, suggest backup code |

---

## Verification Plan

### Backend Testing (`test_electronic_signature.sh`)
```bash
# Test cases:
1. Setup TOTP - verify QR URI and backup codes returned
2. Verify setup - valid code completes, invalid fails
3. Sign without TOTP setup - should fail
4. Sign with items not in production - should fail
5. Sign with wrong TOTP - should fail, track attempts
6. Rate limiting - 5 failures triggers 15-min lockout
7. Sign success - verify is_signed, is_locked, hash created
8. Verify signature - hash matches items snapshot
9. Unlock signed RE - should fail
10. Delete signed RE - should fail
11. Use backup code - works once, consumed after
```

### Manual Testing
1. Setup signature TOTP, save backup codes
2. Create RE with items, mark all as in_production
3. Sign the RE with TOTP code
4. Verify RE shows signature badge
5. Attempt unlock - should fail
6. Verify signature via API endpoint
7. Test lockout by entering wrong codes 5 times
8. Use backup code to recover

---

## Files to Create/Modify

**New Files:**
- `backend/app/core/signature_security.py` - Encryption, TOTP, rate limiting
- `backend/app/models/reporting_effort_signature_history.py`
- `backend/migrations/versions/add_electronic_signature.py`
- `backend/tests/scripts/test_electronic_signature.sh`
- `react-frontend/src/features/settings/SignatureSetupDialog.tsx`
- `react-frontend/src/features/study-management/SignReportingEffortDialog.tsx`

**Modified Files:**
- `backend/app/core/config.py` - Add `SIGNATURE_ENCRYPTION_KEY` setting
- `backend/app/models/user.py` - Add signature TOTP fields (encrypted)
- `backend/app/models/reporting_effort.py` - Add signature fields + relationships
- `backend/app/models/__init__.py` - Export new model
- `backend/app/schemas/reporting_effort.py` - Add signature schemas
- `backend/app/schemas/user.py` - Add signature status schema
- `backend/app/crud/user.py` - Add signature TOTP methods with rate limiting
- `backend/app/crud/reporting_effort.py` - Add sign method
- `backend/app/crud/reporting_effort_item_tracker.py` - Add production check
- `backend/app/api/v1/users.py` - Add signature setup endpoints
- `backend/app/api/v1/reporting_efforts.py` - Add sign/verify endpoints, update unlock
- `backend/app/api/v1/studies.py` - Add deletion protection check
- `react-frontend/src/types/index.ts` - Add signature types
- `react-frontend/src/api/endpoints/users.ts` - Add signature API
- `react-frontend/src/api/endpoints/reporting-efforts.ts` - Add sign/verify API
- `react-frontend/src/features/settings/SettingsPage.tsx` - Add setup section
- `react-frontend/src/stores/websocketStore.ts` - Handle `reporting_effort_signed` event
- `react-frontend/package.json` - Add qrcode.react dependency

---

## Implementation Sequence

1. **Config** - Add `SIGNATURE_ENCRYPTION_KEY` to settings
2. **Database Migration** - Add all new fields and tables
3. **Backend Models** - Add signature fields, relationships, history model
4. **Backend Security** - Create signature_security.py with encryption
5. **Backend CRUD** - Add signature methods with rate limiting
6. **Backend API** - Add endpoints, update unlock with signed check
7. **Frontend Types** - Update TypeScript interfaces
8. **Frontend API** - Add API endpoint functions
9. **Frontend Components** - Create dialogs with backup code display
10. **Frontend Integration** - Add signature controls, WebSocket handling
11. **Testing** - Create comprehensive test script
