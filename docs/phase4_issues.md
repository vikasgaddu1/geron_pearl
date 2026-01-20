# Phase 4 Implementation Issues

This document identifies issues found in the Phase 4 Super Admin Portal implementation.

---

## What's Working Well

- **Super Admin Model**: Separate from User, with MFA fields, lockout logic, audit fields
- **Separate JWT Authentication**: Different secret (`SUPER_ADMIN_JWT_SECRET`), different issuer (`pearl-superadmin`)
- **MFA Implementation**: TOTP with pyotp, backup codes, setup/verify flow
- **Impersonation Token**: 1-hour expiry, includes `super_admin_id` for audit, `read_only` flag
- **Audit Logging**: Impersonation start is logged to audit_log table
- **Dashboard Stats**: Total tenants, active/trialing counts, MRR calculation
- **Tenant List**: Search, status filter, pagination
- **Frontend Login**: MFA support, dark theme, professional UI
- **Frontend Dashboard**: Stats cards, tenant table, impersonation button
- **Impersonation Banner**: Shows tenant name, read-only indicator, exit button
- **API Router**: Properly registered at `/super-admin` prefix

---

## Critical Issues

### 1. Impersonation Token Not Accepted by get_current_user()

**Location**: `backend/app/core/security.py:130-136`

```python
# Verify token type
if payload.get("type") != "access":
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token type",
    )
```

**Problem**: The `get_current_user()` dependency only accepts tokens with `type: "access"`. Impersonation tokens have `type: "impersonation"` and use a different JWT secret (`SUPER_ADMIN_JWT_SECRET`).

**Impact**: When super admin tries to use impersonation token to access `/app/*` routes, they'll get "Invalid token type" error.

**Fix needed**: Update `get_current_user()` to also handle impersonation tokens:
```python
# Try regular token first
try:
    payload = decode_token(token)
    if payload.get("type") == "access":
        user_id = int(payload["sub"])
except JWTError:
    # Try impersonation token
    from app.core.super_admin_security import decode_impersonation_token
    try:
        payload = decode_impersonation_token(token)
        user_id = int(payload["sub"])
        # Store impersonation context for read_only check
    except JWTError:
        raise HTTPException(...)
```

---

### 2. Read-Only Mode Not Enforced

**Location**: Backend - no middleware exists

The impersonation token includes a `read_only` flag, but:

| Component | read_only Checked? |
|-----------|-------------------|
| Token generation | Yes (flag included) |
| Frontend banner | Yes (displays warning) |
| Backend mutations | **NO** |

**Problem**: A super admin with `read_only=True` can still make POST/PUT/DELETE requests.

**Impact**: "Read-only" impersonation can still modify tenant data.

**Fix needed**: Create middleware or dependency:
```python
async def check_impersonation_read_only(request: Request):
    """Block mutations if in read-only impersonation mode."""
    token = get_token_from_request(request)
    if is_impersonation_token(token):
        payload = decode_impersonation_token(token)
        if payload.get("read_only") and request.method in ("POST", "PUT", "PATCH", "DELETE"):
            raise HTTPException(
                status_code=403,
                detail="Read-only impersonation mode - mutations are blocked"
            )
```

---

## Medium Issues

### 3. No Audit Log for Impersonation End

**Location**: `backend/app/core/super_admin_security.py:265-285`

```python
async def log_impersonation_end(...):
    """Log the end of an impersonation session."""
    # This function exists but is NEVER CALLED
```

**Problem**: The `log_impersonation_end()` function is defined but not called when:
- Super admin clicks "Exit Impersonation" (frontend just clears localStorage)
- Impersonation token expires

**Impact**: Incomplete audit trail - we know when impersonation started but not when it ended.

**Fix needed**:
- Frontend should call backend endpoint on exit
- Add `/super-admin/impersonate/end` endpoint that logs and invalidates token

---

### 4. Dashboard Route Not Protected

**Location**: `react-frontend/src/App.tsx:45`

```tsx
<Route path="/admin/dashboard" element={<SuperAdminDashboard />} />
```

**Problem**: The route has no `ProtectedRoute` wrapper. While the component checks for token and redirects, there's a brief moment where someone can see the page shell.

**Expected**:
```tsx
<Route
  path="/admin/dashboard"
  element={
    <SuperAdminProtectedRoute>
      <SuperAdminDashboard />
    </SuperAdminProtectedRoute>
  }
/>
```

---

### 5. Super Admin Token Persists After Browser Close

**Location**: `react-frontend/src/api/endpoints/super-admin.ts:90-91`

```typescript
export const setSuperAdminToken = (token: string) => {
  localStorage.setItem(SUPER_ADMIN_TOKEN_KEY, token);
};
```

**Problem**: Super admin tokens are stored in `localStorage`, which persists across browser sessions.

**Security concern**: For super admin (high-privilege account), `sessionStorage` would be safer.

---

## Minor Issues

### 6. MFA Not Required on All Sensitive Operations

**Location**: `backend/app/api/v1/super_admin.py`

| Endpoint | require_mfa Used? |
|----------|-------------------|
| `/login` | MFA checked inline |
| `/mfa/setup` | No (expected - setting up MFA) |
| `/mfa/verify` | No |
| `/mfa/disable` | MFA token required |
| `/impersonate` | Production check inline |
| `/dashboard/stats` | **No** |
| `/tenants` | **No** |
| `/tenants/{id}` | **No** |

**Problem**: Dashboard and tenant list endpoints don't require MFA in production.

**Expected**: All super admin endpoints (except login/setup) should use `require_mfa` dependency in production.

---

### 7. Default Super Admin Has Known Email

**Location**: `backend/app/models/super_admin.py:126-130`

```python
DEFAULT_SUPER_ADMIN = {
    "email": "superadmin@pearl.local",
    "name": "Super Admin",
}
```

**Problem**: Predictable email. Should be configurable via environment variable.

---

### 8. Impersonation Allows Commenting

**Location**: Not enforced

Even in read-only mode, super admin could potentially add comments which are visible to tenant users.

**Expected**: Read-only impersonation should explicitly block all writes including comments.

---

### 9. No Rate Limiting on Super Admin Login

**Location**: `backend/app/api/v1/super_admin.py:63`

While there's lockout after 5 failed attempts, there's no rate limiting to slow down brute force attempts.

---

### 10. Super Admin Token Shown in Response

**Location**: Frontend stores token, but token appears in network tab

Consider using HttpOnly cookies for super admin authentication for additional security.

---

## Summary

| Issue | Severity | Status |
|-------|----------|--------|
| Impersonation token not accepted | Critical | **FIXED** - Updated `get_current_user()` |
| Read-only mode not enforced | Critical | **FIXED** - Added `ImpersonationReadOnlyMiddleware` |
| No impersonation end audit | Medium | **FIXED** - Added `/impersonate/end` endpoint |
| Dashboard route not protected | Medium | **FIXED** - Created `SuperAdminProtectedRoute` |
| Token in localStorage | Medium | **FIXED** - Changed to `sessionStorage` |
| MFA not required on all endpoints | Low | **FIXED** - Added `require_mfa` dependency |
| Default email predictable | Low | Configuration (not fixed - low priority) |
| Commenting allowed in read-only | Low | **FIXED** - Middleware blocks all mutations |
| No login rate limiting | Low | Not fixed - security hardening (low priority) |
| Token in network response | Low | Best practice (not fixed - low priority) |

---

## Recommended Next Steps

1. **Update get_current_user()** to accept impersonation tokens:
   - Try decoding with super admin secret first
   - If impersonation, check read_only and set request state
   - Fall back to regular token decoding

2. **Create read-only middleware**:
   ```python
   @app.middleware("http")
   async def check_impersonation_readonly(request: Request, call_next):
       if is_mutation(request.method):
           if is_readonly_impersonation(request):
               return JSONResponse(
                   status_code=403,
                   content={"detail": "Read-only mode"}
               )
       return await call_next(request)
   ```

3. **Add impersonation end endpoint**:
   ```python
   @router.post("/impersonate/end")
   async def end_impersonation(
       request: Request,
       super_admin: SuperAdmin = Depends(get_current_super_admin),
       db: AsyncSession = Depends(get_db),
   ):
       await log_impersonation_end(...)
       return {"message": "Impersonation ended"}
   ```

4. **Create SuperAdminProtectedRoute** component for frontend

5. **Add require_mfa to all sensitive endpoints** in production
