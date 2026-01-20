# Phase 5 Implementation Issues

This document identifies issues found in the Phase 5 Sample Data & Onboarding implementation.

---

## What's Working Well

- **Sample Data Service**: `services/sample_data.py` with seed, clear, and reset functions
- **Sample Data Definitions**: Studies, packages, text elements with realistic data
- **Tenant Data API**: Endpoints for checking, seeding, resetting, and clearing data
- **Frontend API Client**: `tenant-data.ts` with type-safe functions
- **Router Registration**: `/tenant/*` endpoints properly registered
- **Tenant Model Updated**: `onboarding_completed` and `sample_data_seeded` fields added

---

## Critical Issues

### 1. Sample Data Not Seeded on Tenant Creation

**Location**: `backend/app/api/v1/billing.py:279-281`

```python
# TODO: Seed sample data for the new tenant
# This will be implemented in Phase 5
# await seed_sample_data(db, tenant.id)
```

**Problem**: The webhook handler still has the sample data seeding commented out. New tenants get an empty workspace.

**Impact**: Phase 5 was supposed to enable automatic sample data seeding, but it's not wired up.

**Fix needed**:
```python
from app.services.sample_data import seed_sample_data

# After tenant and user creation
await seed_sample_data(db, tenant.id)
tenant.sample_data_seeded = True
await db.commit()
```

---

### 2. Wrong item_type Values in Sample Data

**Location**: `backend/app/services/sample_data.py:63-86`

```python
{"item_name": "t-ae-summary", "item_type": "table"},
{"item_name": "f-ae-overview", "item_type": "figure"},
{"item_name": "l-ae-listing", "item_type": "listing"},
```

**Problem**: The `ItemType` enum only has `TLF` and `Dataset` values:
```python
class ItemType(str, Enum):
    TLF = "TLF"
    Dataset = "Dataset"
```

**Impact**: Sample data seeding will fail with enum validation error.

**Fix needed**: Update sample data to use valid enum values:
```python
{"item_name": "t-ae-summary", "item_type": ItemType.TLF},
{"item_name": "adae", "item_type": ItemType.Dataset},
```

---

### 3. Migration Has No down_revision

**Location**: `backend/migrations/versions/add_tenant_onboarding_fields.py:17`

```python
down_revision: Union[str, None] = None
```

**Problem**: The migration is not connected to the migration chain. It's set as a base migration.

**Impact**: Running `alembic upgrade head` won't apply this migration correctly. It may create a new branch or be skipped entirely.

**Fix needed**: Set `down_revision` to the latest migration in the chain.

---

## Medium Issues

### 4. Duplicate Onboarding Flags

**Locations**:
- `models/tenant.py:105-116` - `onboarding_completed` and `sample_data_seeded`
- `models/tenant_settings.py:72-83` - `onboarding_completed` and `sample_data_active`

**Problem**: Both Tenant and TenantSettings have overlapping fields:

| Tenant | TenantSettings |
|--------|----------------|
| `onboarding_completed` | `onboarding_completed` |
| `sample_data_seeded` | `sample_data_active` |

**Impact**: Confusion about which to check/update. They could get out of sync.

**Fix needed**: Remove duplicates. Keep on TenantSettings since that's the settings model, or keep on Tenant since it's more accessible.

---

### 5. No UI for Sample Data Management

**Location**: Frontend - no component exists

The `tenant-data.ts` API client exists but no component uses it:

| Endpoint | API Function | UI Component |
|----------|--------------|--------------|
| `/tenant/sample-data/status` | `getSampleDataStatus()` | None |
| `/tenant/sample-data/seed` | `seedSampleData()` | None |
| `/tenant/reset-to-sample` | `resetToSampleData()` | None |
| `/tenant/clear-all` | `clearAllData()` | None |

**Expected**: Add UI in Settings page to:
- Show if sample data exists
- Button to seed sample data (if none exists)
- Button to reset to sample data (with confirmation)
- Button to clear all data (with strong warning)

---

### 6. tenant.sample_data_seeded Not Updated After Seeding

**Location**: `backend/app/services/sample_data.py:128-223`

The `seed_sample_data()` function seeds data but doesn't update `tenant.sample_data_seeded = True`.

**Impact**: The flag won't reflect actual state.

**Fix needed**: Accept tenant object or update tenant in the function:
```python
# At end of seed_sample_data
tenant = await db.get(Tenant, tenant_id)
if tenant:
    tenant.sample_data_seeded = True
```

---

### 7. No Reporting Efforts in Sample Data

**Location**: `backend/app/services/sample_data.py:34-57`

Sample data creates:
- Studies
- Database Releases

But does NOT create:
- Reporting Efforts (attached to database releases)
- Reporting Effort Items
- Trackers

**Impact**: New users won't see the tracker functionality which is a key feature.

**Expected**: Add reporting efforts with items and trackers to demonstrate the full workflow.

---

## Minor Issues

### 8. No Import Statement for ItemType

**Location**: `backend/app/services/sample_data.py`

The file imports `PackageItem` but uses string values for `item_type` instead of importing and using `ItemType` enum.

---

### 9. Text Elements Should Have Optional Reference IDs

Sample text elements are created without linking to any specific package or study. Consider adding relationships.

---

### 10. Check_has_sample_data Only Checks Studies

**Location**: `backend/app/services/sample_data.py:326-346`

```python
async def check_has_sample_data(...) -> bool:
    result = await db.execute(
        select(Study)
        .where(Study.tenant_id == tenant_id)
        .where(Study.study_label.like("DEMO-%"))
        .limit(1)
    )
    return result.scalar_one_or_none() is not None
```

**Problem**: Only checks for DEMO- studies. If user keeps studies but clears packages/text elements, it still reports as "has sample data".

---

## Summary

| Issue | Severity | Status |
|-------|----------|--------|
| Sample data not seeded on tenant creation | Critical | **FIXED** - Wired up in billing webhook |
| Wrong item_type enum values | Critical | **FIXED** - Using ItemType enum |
| Migration has no down_revision | Critical | **FIXED** - Set to `add_rls_policies` |
| Duplicate onboarding flags | Medium | **FIXED** - Removed from TenantSettings |
| No UI for sample data management | Medium | Deferred to Phase 6 |
| sample_data_seeded not updated | Medium | **FIXED** - Updated in seed function |
| No reporting efforts in sample data | Medium | **FIXED** - Added reporting efforts |
| Missing ItemType import | Low | **FIXED** - Imported from enums |
| Text elements not linked | Low | Enhancement (not fixed - low priority) |
| check_has_sample_data incomplete | Low | Edge case (not fixed - low priority) |

---

## Recommended Next Steps

1. **Fix the item_type values** in sample data:
   ```python
   from app.models.enums import ItemType

   SAMPLE_PACKAGES = [
       {
           "package_name": "PKG-SAFETY",
           "items": [
               {"item_name": "t-ae-summary", "item_type": ItemType.TLF},
               {"item_name": "adae", "item_type": ItemType.Dataset},
           ],
       },
   ]
   ```

2. **Wire up sample data seeding** in billing webhook:
   ```python
   from app.services.sample_data import seed_sample_data

   # After creating admin user
   await seed_sample_data(db, tenant.id)
   tenant.sample_data_seeded = True
   ```

3. **Fix migration dependency**:
   ```python
   down_revision = 'add_rls_policies'  # or the actual latest migration
   ```

4. **Add Reporting Efforts to sample data** for complete demo

5. **Create Settings UI section** for sample data management with:
   - Status display
   - Seed/Reset/Clear buttons
   - Appropriate warnings and confirmations

6. **Remove duplicate flags** - keep fields only in one place (Tenant or TenantSettings)
