# Phase 1 Implementation Issues

This document identifies issues found in the Phase 1 multi-tenancy implementation.

---

## Critical Issues

### 1. RLS Not Implemented

**Status**: `phase1-rls` marked as PARTIAL but **no RLS SQL exists**

The migration file `add_multi_tenancy_foundation.py` creates tables and adds `tenant_id` columns, but does NOT contain any Row-Level Security implementation:

- No `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
- No `ALTER TABLE ... FORCE ROW LEVEL SECURITY`
- No `CREATE POLICY tenant_isolation_*`
- No `GRANT` statements for roles

**Expected** (from plan):
```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_users ON users
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::int)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::int);
```

**Impact**: Without RLS, tenant data isolation relies entirely on application-level filtering, which is error-prone.

---

### 2. No BYPASSRLS Role for Super Admin

**Status**: Missing entirely

The plan specifies creating a `pearl_super_admin` database role with `BYPASSRLS` privilege for super admin operations. This is not implemented.

**Expected** (from plan):
```sql
CREATE ROLE pearl_super_admin WITH BYPASSRLS LOGIN PASSWORD 'configured-via-env';
```

**Also missing**:
- `SUPER_ADMIN_DATABASE_URL` configuration in `config.py`
- Separate database engine/session for super admin operations in `session.py`

---

### 3. Notifications Table Missing tenant_id

**Status**: Not implemented

The plan specifies `notifications` should have `tenant_id`, but:
- The migration doesn't add `tenant_id` to `notifications` table
- The `Notification` model (`models/notification.py`) has no `tenant_id` field

**Impact**: Notification queries won't be tenant-scoped.

---

### 4. AppSettings Table Missing tenant_id

**Status**: Not implemented

The plan specifies `app_settings` should have `tenant_id`, but:
- The migration doesn't add `tenant_id` to `app_settings` table
- The `AppSettings` model has no `tenant_id` field

**Impact**: Application settings are global instead of per-tenant.

---

## Medium Issues

### 5. Username Has Global Unique Constraint

**Location**: `models/user.py:51`
```python
username = Column(String, unique=True, index=True, nullable=False)
```

**Problem**: Username uniqueness is enforced globally, not per-tenant. This means:
- Tenant A cannot have user "admin" if Tenant B already has one
- Two different organizations cannot have the same usernames

**Expected**: Either:
- Remove global unique constraint, add `UniqueConstraint('tenant_id', 'username')`
- Or rely on email (per-tenant unique) as the login identifier

---

### 6. TenantContextMiddleware Not Registered

**Location**: `core/tenant.py` defines `TenantContextMiddleware`

**Problem**: The middleware is defined but NOT registered in `main.py`. The grep for `TenantContextMiddleware` in `main.py` returns no matches.

**Impact**: Tenant context is not automatically extracted from JWT on each request. The `current_tenant_id` context variable won't be populated.

**Fix needed**: Add to `main.py`:
```python
from app.core.tenant import TenantContextMiddleware
app.add_middleware(TenantContextMiddleware)
```

---

### 7. Type Mismatch in Models

**Location**: `models/tenant_settings.py`, `models/subscription_plan.py`

Several columns use `Integer` column type but have `bool` type annotation:

```python
# tenant_settings.py
onboarding_completed: Mapped[bool] = mapped_column(Integer, ...)
sample_data_active: Mapped[bool] = mapped_column(Integer, ...)

# subscription_plan.py
is_active: Mapped[bool] = mapped_column(Integer, ...)
```

**Problem**: SQLite compatibility workaround, but creates type confusion. PostgreSQL supports native `Boolean`.

---

## Minor Issues

### 8. Missing Composite Index on audit_log.action

The migration creates indexes for `(tenant_id, created_at)` and `(tenant_id, table_name)` but common queries also filter by `action`. Consider:
```sql
CREATE INDEX ix_audit_log_tenant_action ON audit_log (tenant_id, action);
```

---

### 9. No Tests for New Models

No test scripts found for:
- Tenant CRUD operations
- SuperAdmin CRUD operations
- SubscriptionPlan CRUD operations
- TenantSettings CRUD operations

The test strategy document recommends curl-based tests in `tests/scripts/`.

---

### 10. Default Tenant Has No Plan Assigned

The migration creates a default tenant:
```sql
INSERT INTO tenants (id, name, display_name, subscription_status, is_active)
VALUES (1, 'default', 'Default Tenant', 'active', 1)
```

But `plan_id` is not set (NULL). Should assign to a default plan (e.g., 'professional' for existing users).

---

## Summary

| Issue | Severity | Status |
|-------|----------|--------|
| RLS not implemented | Critical | Missing |
| BYPASSRLS role missing | Critical | Missing |
| notifications.tenant_id missing | Critical | Missing |
| app_settings.tenant_id missing | Critical | Missing |
| username global unique constraint | Medium | Bug |
| TenantContextMiddleware not registered | Medium | Missing |
| Type mismatch (Integer vs Boolean) | Low | Code smell |
| Missing composite index on action | Low | Optimization |
| No tests for new models | Low | Missing |
| Default tenant has no plan | Low | Data issue |

---

## Recommended Next Steps

1. **Create RLS migration** (`add_rls_policies.py`):
   - Enable RLS on all tenant-aware tables
   - Create isolation policies
   - Create BYPASSRLS role

2. **Add tenant_id to missing tables**:
   - `notifications`
   - `app_settings`

3. **Fix username uniqueness**:
   - Add `UniqueConstraint('tenant_id', 'username')`
   - Update migration downgrade to restore global unique

4. **Register middleware** in `main.py`

5. **Create test scripts** for multi-tenancy CRUD operations
