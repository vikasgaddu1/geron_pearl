# Phase 2 Implementation Issues

This document identifies issues found in the Phase 2 Stripe integration implementation.

---

## Critical Issues

### 1. Email Functions Not Called (Multiple TODOs)

**Location**: `api/v1/billing.py`

The webhook handler has TODO comments but doesn't actually call the email functions:

```python
# Line 239-240
# TODO: Send welcome email with password reset link
# await send_welcome_email(email, tenant.display_name, temp_password)

# Line 267
# TODO: Send payment warning email

# Line 289
# TODO: Send cancellation confirmation email

# Line 312
# TODO: Send payment failed email
```

**Impact**: New signups won't receive their login credentials. Payment failures won't be communicated to customers.

**The email functions exist** in `core/email.py`:
- `send_welcome_email()`
- `send_payment_failed_email()`
- `send_subscription_canceled_email()`
- `send_trial_ending_email()`

**Fix needed**: Import and call these functions in the webhook handler.

---

### 2. TenantSettings Not Created with New Tenant

**Location**: `api/v1/billing.py:213-224` and `crud/tenant.py:16-31`

When a new tenant is created via Stripe webhook, `TenantSettings` is NOT created alongside it.

**Current code** (billing.py):
```python
tenant = await tenant_crud.create(db, obj_in=TenantCreate(...))
# TenantSettings NOT created!
```

**Impact**:
- New tenants will have NULL settings
- The `tenant.settings` relationship will return None
- Queries expecting TenantSettings will fail

**Fix needed**: Either:
1. Create TenantSettings in the billing.py webhook after tenant creation
2. Or modify `TenantCRUD.create()` to automatically create default settings

---

### 3. Sample Data Seeding Not Implemented

**Location**: `api/v1/billing.py:242-243`

```python
# TODO: Seed sample data for the new tenant
# await seed_sample_data(db, tenant.id)
```

**Impact**: New tenants get an empty workspace with no demo data to explore.

**Missing**: The `db/sample_data.py` file doesn't exist at all.

---

### 4. Subscription Access Control Not Applied

**Location**: `core/subscription.py`

The following dependencies are defined but **never used**:

| Dependency | Purpose | Usage in API routes |
|------------|---------|---------------------|
| `require_active_subscription` | Block access for canceled/unpaid | Not used anywhere |
| `check_user_limit` | Enforce user quota before creating users | Not used in users.py |
| `check_study_limit` | Enforce study quota before creating studies | Not used in studies.py |
| `SubscriptionMiddleware` | Add subscription headers to responses | Not registered in main.py |

**Impact**:
- Canceled tenants can still access the application
- Tenants can exceed their plan limits
- No subscription status warnings shown to users

**Fix needed**:
1. Add `require_active_subscription` to protected routes
2. Add `check_user_limit` to user creation endpoint
3. Add `check_study_limit` to study creation endpoint
4. Register `SubscriptionMiddleware` in main.py

---

## Medium Issues

### 5. Missing `invoice.paid` Webhook Handler

**Location**: `api/v1/billing.py`

The plan specifies handling `invoice.paid` events, but it's not implemented:

**Expected events** (from plan):
- `checkout.session.completed` ✓
- `customer.subscription.updated` ✓
- `customer.subscription.deleted` ✓
- `invoice.payment_failed` ✓
- `invoice.paid` ✗ Missing

**Impact**: Can't detect when a past_due subscription becomes active again after successful payment.

---

### 6. Email Check is Global, Not Per-Tenant

**Location**: `api/v1/billing.py:106-114`

```python
result = await db.execute(
    select(User).where(User.email == signup_data.email)
)
existing_user = result.scalar_one_or_none()
if existing_user:
    raise HTTPException(...)
```

**Problem**: This prevents the same email from being used across different tenants. In multi-tenant SaaS, it's common to allow the same person to have accounts in multiple organizations.

**Expected**: Either allow duplicate emails across tenants, or clearly document this as a design decision.

---

### 7. Stripe API Calls are Synchronous

**Location**: `core/stripe.py`

All Stripe API calls use the synchronous Stripe SDK but are wrapped in async functions:

```python
async def create_checkout_session(...):
    session = stripe.checkout.Session.create(...)  # Synchronous!
    return session
```

**Impact**: These synchronous calls will block the event loop. For high-traffic scenarios, this could cause performance issues.

**Fix**: Use `stripe` library with `asyncio` or run in thread pool:
```python
from asyncio import to_thread
session = await to_thread(stripe.checkout.Session.create, ...)
```

---

### 8. No Webhook Event Logging

**Location**: `api/v1/billing.py`

Stripe webhook events are processed but not logged to the database.

**Missing**:
- No `WebhookEvent` model to track processed events
- No audit trail of billing events
- Difficult to debug webhook issues

**The schema exists** (`schemas/billing.py:99-106`) but no corresponding model or logging.

---

## Minor Issues

### 9. Hardcoded "professional" Plan Check

**Location**: `api/v1/billing.py:74`

```python
is_popular=(plan.name == "professional"),  # Hardcoded!
```

**Problem**: If plan names change, this breaks.

**Better approach**: Add `is_popular` or `is_featured` column to `SubscriptionPlan` model.

---

### 10. Storage Calculation Placeholder

**Location**: `api/v1/billing.py:385-387`

```python
storage_used_mb=0,  # TODO: Calculate actual storage
storage_limit_mb=max_storage,
storage_remaining_mb=max_storage,  # TODO: Calculate actual remaining
```

**Impact**: Storage usage always shows as 0. Users can't see actual usage.

---

### 11. Missing `cancel_at_period_end` from Stripe

**Location**: `api/v1/billing.py:375`

```python
cancel_at_period_end=False,  # TODO: Get from Stripe
```

**Impact**: Can't show users if their subscription is set to cancel.

---

### 12. No Frontend Signup Page Component

The backend `/signup/initiate` endpoint exists, but there's no corresponding frontend `SignupPage` component listed in the implementation docs.

---

## Summary

| Issue | Severity | Status |
|-------|----------|--------|
| Email functions not called | Critical | **FIXED** - Emails now sent |
| TenantSettings not created | Critical | **FIXED** - Created with tenant |
| Sample data seeding | Critical | DEFERRED - Phase 5 |
| Subscription access control not applied | Critical | **FIXED** - Added to routes |
| invoice.paid handler | Medium | **FIXED** - Handler added |
| Email check is global | Medium | Design decision |
| Stripe API blocking | Medium | **FIXED** - Using to_thread |
| No webhook logging | Medium | Missing |
| Hardcoded plan name | Low | **FIXED** - Using is_popular column |
| Storage calculation | Low | Placeholder |
| cancel_at_period_end | Low | Placeholder |
| Frontend signup page | Low | Missing (Phase 3)

---

## Recommended Next Steps

1. **Wire up email functions** in billing webhook handler:
   ```python
   from app.core.email import send_welcome_email, send_payment_failed_email
   # Then call them where TODOs are
   ```

2. **Create TenantSettings** when creating tenant:
   ```python
   # After tenant creation
   from app.models.tenant_settings import TenantSettings, DEFAULT_TENANT_SETTINGS
   settings = TenantSettings(tenant_id=tenant.id, **DEFAULT_TENANT_SETTINGS)
   db.add(settings)
   ```

3. **Apply subscription middleware** to protected routes:
   ```python
   # In studies.py create endpoint
   async def create_study(
       ...,
       _: None = Depends(require_active_subscription),
       __: None = Depends(check_study_limit),
   ):
   ```

4. **Create sample_data.py** module with demo studies, packages, etc.

5. **Add invoice.paid handler** to reset grace_period_ends_at when payment succeeds.
