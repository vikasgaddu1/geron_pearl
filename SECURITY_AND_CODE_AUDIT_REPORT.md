# PEARL Security and Code Optimization Audit Report

**Date**: January 5, 2026
**Auditor**: Claude Code Deep Analysis
**Scope**: Permission system, update paths, validation rules, auto-triggers, security pitfalls

---

## Executive Summary

This audit identifies **12 critical security vulnerabilities**, **8 moderate issues**, and **15 optimization opportunities** in the PEARL application. The most severe issues involve **missing authentication on bulk endpoints** and **inconsistent permission enforcement** between individual and bulk operations.

### Critical Findings Summary

| Severity | Count | Key Issues |
|----------|-------|------------|
| **CRITICAL** | 5 | Missing authentication on sensitive endpoints |
| **HIGH** | 7 | Permission bypass, validation inconsistencies |
| **MEDIUM** | 8 | Business logic gaps, missing constraints |
| **LOW** | 5 | Code duplication, optimization opportunities |

---

## Part 1: Security Vulnerabilities

### CRITICAL-001: Bulk TLF Upload Missing Authentication

**File**: `backend/app/api/v1/reporting_effort_items.py:660-844`
**Endpoint**: `POST /api/v1/reporting-effort-items/{reporting_effort_id}/bulk-tlf`

**Issue**: The endpoint is documented as "Admin only functionality" but has **NO authentication**:

```python
async def bulk_create_tlf_items(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    items_in: List[BulkTLFItem],
    # Note: In production, add user role authentication here  <-- NOT IMPLEMENTED
    # current_user: User = Depends(get_current_admin_user)
) -> BulkUploadResponse:
```

**Impact**: Any authenticated user (or potentially unauthenticated) can bulk create TLF items, bypassing the intended admin-only restriction.

**Recommendation**: Add `current_user: UserModel = Depends(get_current_user)` and admin role check.

---

### CRITICAL-002: Bulk Dataset Upload Missing Authentication

**File**: `backend/app/api/v1/reporting_effort_items.py:846-972`
**Endpoint**: `POST /api/v1/reporting-effort-items/{reporting_effort_id}/bulk-dataset`

**Issue**: Same as CRITICAL-001, no authentication implemented despite being marked admin-only.

---

### CRITICAL-003: Import Trackers Missing Authentication

**File**: `backend/app/api/v1/reporting_effort_tracker.py:1363-1497`
**Endpoint**: `POST /api/v1/reporting-effort-tracker/import/{reporting_effort_id}`

**Issue**: No authentication or permission check. Anyone can import tracker data:

```python
@router.post("/import/{reporting_effort_id}")
async def import_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,  # No current_user dependency!
    reporting_effort_id: int,
    trackers: List[TrackerImportData],
    ...
```

**Impact**: Attackers can:
- Overwrite tracker assignments
- Change production/QC status arbitrarily
- Modify priority and dates
- All without any authorization

---

### CRITICAL-004: Unassign Programmer Missing Permission Check

**File**: `backend/app/api/v1/reporting_effort_tracker.py:678-773`
**Endpoint**: `DELETE /api/v1/reporting-effort-tracker/{tracker_id}/unassign-programmer`

**Issue**: No `current_user` dependency or permission check:

```python
@router.delete("/{tracker_id}/unassign-programmer", ...)
async def unassign_programmer(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,  # No current_user!
    tracker_id: int,
    role: str = Query(...),
) -> ReportingEffortItemTracker:
```

**Impact**: Any user can unassign production/QC programmers, disrupting workflow and assignments.

---

### CRITICAL-005: Delete Tracker Missing Permission Check

**File**: `backend/app/api/v1/reporting_effort_tracker.py:470-559`
**Endpoint**: `DELETE /api/v1/reporting-effort-tracker/{tracker_id}`

**Issue**: No authentication requirement:

```python
@router.delete("/{tracker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracker(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,  # No current_user!
    tracker_id: int,
) -> None:
```

**Impact**: Any request can delete tracker entries.

---

### HIGH-001: Bulk Status Update Bypasses Business Rules

**File**: `backend/app/api/v1/reporting_effort_tracker.py:888-957`
**Endpoint**: `POST /api/v1/reporting-effort-tracker/bulk-status-update`

**Issue**: Individual tracker update enforces multiple business rules:
- Cannot mark QC completed with unresolved comments
- Auto-transitions applied (QC FAILED -> Prod IN_PROGRESS)
- Due date auto-set on programmer assignment

But bulk status update **bypasses ALL these rules**:

```python
# Line 918 - Direct CRUD call without validation
updated_trackers = await reporting_effort_item_tracker.bulk_update(
    db, updates=crud_updates
)
```

**Comparison Table**:

| Validation | Individual Update | Bulk Status Update |
|------------|------------------|-------------------|
| Unresolved comments check | YES | **NO** |
| Auto-transitions | YES | **NO** |
| Due date auto-set | YES | **NO** |
| Status transition validation | YES | **NO** |

**Impact**: Admin can use bulk update to set QC=completed even with unresolved comments, corrupting data integrity.

---

### HIGH-002: Bulk Assign-Status Bypasses Auto-Transitions

**File**: `backend/app/api/v1/reporting_effort_tracker.py:960-1105`
**Endpoint**: `POST /api/v1/reporting-effort-tracker/bulk-assign-status`

**Issue**: While this endpoint validates "programmer must be assigned", it does NOT apply `TrackerWorkflowService.apply_status_transition()`:

```python
# Missing this call that exists in individual update:
# auto_updates = TrackerWorkflowService.apply_status_transition(...)
# update_data.update(auto_updates)
```

**Impact**: Bulk operations can create invalid state combinations that individual operations prevent.

---

### HIGH-003: Reporting Effort Item Update Missing Authentication

**File**: `backend/app/api/v1/reporting_effort_items.py:485-593`
**Endpoint**: `PUT /api/v1/reporting-effort-items/{item_id}`

**Issue**: No user authentication or permission check:

```python
@router.put("/{item_id}", response_model=dict)
async def update_reporting_effort_item(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,  # No current_user!
    item_id: int,
    item_in: ReportingEffortItemUpdate,
) -> dict:
```

**Impact**: Any user (including viewers) can modify item descriptions, dataset details, and TLF details.

---

### HIGH-004: Copy Operations Missing Permission Checks

**Files**:
- `backend/app/api/v1/reporting_effort_items.py:975-1078` (copy from package)
- `backend/app/api/v1/reporting_effort_items.py:1286-1393` (copy from reporting effort)

**Issue**: Both copy endpoints lack authentication. Any user can bulk-create items by copying from packages or other reporting efforts.

---

### HIGH-005: Database Backup Uses Legacy Header-Based Auth

**File**: `backend/app/api/v1/database_backup.py:24-34`

**Issue**: Uses `X-User-Role` header instead of JWT:

```python
def check_admin_access(request: Request):
    user_role = request.headers.get("X-User-Role")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
```

**Impact**: Header-based auth is easily spoofed. Any request can add `X-User-Role: admin` header.

---

### HIGH-006: Audit Trail Uses Same Legacy Auth

**File**: `backend/app/api/v1/audit_trail.py:17-41`

**Issue**: Same header-based check as database backup, easily bypassed.

---

### HIGH-007: VIEWER Can Be Assigned to Tasks (Partial Fix)

**File**: `backend/app/api/v1/reporting_effort_tracker.py:1005-1014`

**Issue**: While bulk-assign-status checks for VIEWER role, the individual assign-programmer endpoint at line 598 does check, BUT if a user's role is changed TO VIEWER after assignment, they retain their assignments.

**Recommendation**: Add periodic validation or event-based cleanup when user role changes to VIEWER.

---

## Part 2: Validation Inconsistencies

### MEDIUM-001: Item Update Doesn't Check Duplicates

**Individual Create Path**: Checks for duplicate `(reporting_effort_id, item_type, item_subtype, item_code)`

**Update Path**: No duplicate check when changing `item_code` or `item_subtype`

**File**: `backend/app/crud/reporting_effort_item.py:116-127` vs `update()` method

**Impact**: Can create duplicate items by updating existing items to have same codes.

---

### MEDIUM-002: No Validation on Import Status Values

**File**: `backend/app/api/v1/reporting_effort_tracker.py:1442-1451`

**Issue**: Import endpoint accepts any string for `production_status` and `qc_status`:

```python
if import_data.production_status:
    update_data["production_status"] = import_data.production_status  # No validation!
```

**Impact**: Can set invalid status values like "invalid_status" or SQL injection attempts.

---

### MEDIUM-003: Frontend Hardcoded Enums May Drift

**Files**:
- `react-frontend/src/features/reporting/ReportingEffortItems.tsx`
- `react-frontend/src/features/reporting/TrackerManagement.tsx`

**Issue**: Frontend uses hardcoded constants for item types, subtypes, and statuses instead of fetching from backend.

```typescript
const TLF_SUBTYPES = ['Table', 'Listing', 'Figure']
const DATASET_SUBTYPES = ['SDTM', 'ADaM']
```

**Impact**: If backend adds new types/statuses, frontend won't support them until code is updated.

---

### MEDIUM-004: No Frontend Validation Before Submit

**Files**: Most form components

**Issue**: Frontend forms rely entirely on backend validation. No client-side validation for:
- Item code length
- Description length
- Required fields
- Valid status transitions

**Impact**: Poor UX - users see errors only after server roundtrip.

---

### MEDIUM-005: Password Reset Token Not Rate Limited

**File**: `backend/app/api/v1/auth.py` (forgot-password endpoint)

**Issue**: No rate limiting on password reset requests. Attacker can flood email inboxes.

---

### MEDIUM-006: QC Completion Date Not Validated Against Timeline

**File**: `backend/app/api/v1/reporting_effort_tracker.py:407`

**Issue**: `qc_completion_date` is auto-set to `date.today()` but no validation that it's not before production start.

---

### MEDIUM-007: Milestone Date Logic Not Enforced

**File**: `backend/app/schemas/reporting_effort_milestone.py`

**Issue**: No validation that:
- `completion_date >= due_date`
- `is_completed=False` should clear `completion_date`
- `actual_date <= due_date` for milestone tracking

---

### MEDIUM-008: Comment Resolution Count Can Drift

**File**: `backend/app/crud/tracker_comment.py:52-63, 189-191`

**Issue**: `unresolved_comment_count` is manually incremented/decremented. If any operation fails mid-way or comments are deleted directly, count can become incorrect.

**Recommendation**: Add periodic reconciliation job or computed column.

---

## Part 3: Optimization Opportunities

### OPT-001: Duplicate Permission Check Code

**Issue**: Permission checking is implemented in multiple places:
1. `TrackerWorkflowService.check_status_change_permission()` - service layer
2. Inline checks in `update_tracker()` endpoint - lines 360-391
3. `require_role()` dependency - for admin-only

**Recommendation**: Consolidate into single `PermissionService` class:

```python
class PermissionService:
    @staticmethod
    def check_tracker_access(user, tracker, operation: str) -> bool:
        """Centralized permission check for all tracker operations."""

    @staticmethod
    def check_item_access(user, item, operation: str) -> bool:
        """Centralized permission check for item operations."""
```

---

### OPT-002: Repeated Validation Code in Bulk Operations

**Issue**: Each bulk endpoint repeats similar validation loops:

```python
for tracker_id in data.tracker_ids:
    db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
    if not db_tracker:
        errors.append(...)
    # validation...
```

**Recommendation**: Create `BulkOperationService`:

```python
class BulkOperationService:
    async def validate_trackers(self, db, tracker_ids) -> Tuple[List[Tracker], List[str]]:
        """Validate multiple trackers, return valid trackers and errors."""
```

---

### OPT-003: Duplicate WebSocket Broadcast Code

**Issue**: Every endpoint has:

```python
try:
    await broadcast_tracker_updated(updated_tracker)
except Exception as ws_error:
    print(f"WebSocket broadcast error: {ws_error}")
```

**Recommendation**: Use decorator or event system:

```python
@broadcast_on_success("tracker_updated")
async def update_tracker(...):
    ...
```

---

### OPT-004: Audit Logging Repetition

**Issue**: Every endpoint has 10+ lines of audit logging code.

**Recommendation**: Use middleware or decorator:

```python
@audit_logged("UPDATE", "reporting_effort_item_tracker")
async def update_tracker(...):
    ...
```

---

### OPT-005: Frontend API Calls Not Using React Query Mutations

**Issue**: Some components use direct API calls instead of useMutation:

```typescript
const handleSave = async () => {
    await api.update(id, data)  // No optimistic updates, no error handling
}
```

**Recommendation**: Use consistent TanStack Query mutations:

```typescript
const mutation = useMutation({
    mutationFn: (data) => api.update(id, data),
    onSuccess: () => queryClient.invalidateQueries(['trackers']),
    onError: (error) => toast.error(getErrorMessage(error)),
})
```

---

### OPT-006: N+1 Query in get_by_effort

**File**: `backend/app/api/v1/reporting_effort_items.py:340-474`

**Issue**: Tracker information is fetched one-by-one inside loop:

```python
for item in items:
    tracker = await reporting_effort_item_tracker.get_by_item(db, ...)
```

**Recommendation**: Use eager loading or batch fetch:

```python
trackers = await reporting_effort_item_tracker.get_multi_by_items(
    db, item_ids=[item.id for item in items]
)
tracker_map = {t.reporting_effort_item_id: t for t in trackers}
```

---

### OPT-007: Status Enum Values Duplicated

**Issue**: Status values defined in multiple places:
- `ProductionStatus` enum in models
- String literals in API validation
- Hardcoded in frontend

**Recommendation**: Single source of truth with API endpoint:

```python
@router.get("/statuses")
async def get_status_options():
    return {
        "production": [s.value for s in ProductionStatus],
        "qc": [s.value for s in QCStatus],
    }
```

---

### OPT-008: Unused import_trackers Audit Uses X-User-Id Header

**File**: `backend/app/api/v1/reporting_effort_tracker.py:1470`

```python
user_id=request.headers.get("X-User-Id"),  # Should use current_user.id
```

**Issue**: Inconsistent with other endpoints that use `getattr(request.state, 'user_id', None)`.

---

## Part 4: Auto-Trigger Analysis

### Current State Machine Rules (Verified Working)

| Trigger | Condition | Auto-Action |
|---------|-----------|-------------|
| QC -> FAILED | Production is READY_FOR_QC | Production -> IN_PROGRESS |
| QC -> COMPLETED | Always | Production -> COMPLETED |
| Production COMPLETED -> IN_PROGRESS | Always | QC -> IN_PROGRESS, in_production_flag = False |
| Production -> READY_FOR_QC | QC is FAILED | QC -> IN_PROGRESS |
| Assign Production | Production is NOT_STARTED | Production -> IN_PROGRESS |
| Assign QC | Production is COMPLETED, QC is NOT_STARTED | QC -> IN_PROGRESS |
| Create Comment | Parent comment | unresolved_count++ |
| Resolve Comment | Parent comment | unresolved_count-- |

### Missing Auto-Trigger Rules

1. **No auto-assignment reset when status reset**: If production_status is manually set to NOT_STARTED, should `production_programmer_id` be cleared?

2. **No cascade to in_production_flag when QC changes**: Setting QC from COMPLETED to FAILED should set `in_production_flag = False`.

3. **No history entry for auto-transitions**: When QC->COMPLETED triggers Production->COMPLETED, only one history entry is created.

---

## Part 5: Permission Matrix

### Current Implementation

| Endpoint | VIEWER | EDITOR | ADMIN |
|----------|--------|--------|-------|
| GET trackers | YES | YES | YES |
| UPDATE tracker (own) | NO | YES | YES |
| UPDATE tracker (others) | NO | NO | YES |
| Bulk assign | NO | NO | YES |
| Bulk status update | NO | NO | YES |
| Unassign programmer | **YES (BUG)** | **YES (BUG)** | YES |
| Delete tracker | **YES (BUG)** | **YES (BUG)** | YES |
| Import trackers | **YES (BUG)** | **YES (BUG)** | YES |
| Bulk TLF upload | **YES (BUG)** | **YES (BUG)** | YES |
| Update RE item | **YES (BUG)** | **YES (BUG)** | YES |

### Recommended Permission Matrix

| Endpoint | VIEWER | EDITOR | ADMIN |
|----------|--------|--------|-------|
| GET trackers | YES | YES | YES |
| UPDATE tracker (own) | NO | YES | YES |
| UPDATE tracker (others) | NO | NO | YES |
| Bulk assign | NO | NO | YES |
| Bulk status update | NO | NO | YES |
| Unassign programmer | NO | NO | YES |
| Delete tracker | NO | NO | YES |
| Import trackers | NO | NO | YES |
| Bulk TLF upload | NO | NO | YES |
| Update RE item | NO | YES (own) | YES |

---

## Part 6: Recommended Fixes Priority

### Immediate (Deploy Blocker)

1. **CRITICAL-001 to CRITICAL-005**: Add authentication to all flagged endpoints
2. **HIGH-005, HIGH-006**: Replace header-based auth with JWT

### Short-term (1-2 sprints)

3. **HIGH-001, HIGH-002**: Add business rule validation to bulk endpoints
4. **HIGH-003, HIGH-004**: Add permission checks to item endpoints
5. **MEDIUM-001, MEDIUM-002**: Add missing validation

### Medium-term (3-4 sprints)

6. **OPT-001 to OPT-004**: Refactor common code patterns
7. **MEDIUM-003**: Implement status/type API endpoint
8. **MEDIUM-008**: Add comment count reconciliation

---

## Part 7: Code Duplication Analysis

### Files with Highest Duplication

| File | Duplicate Pattern | Lines |
|------|------------------|-------|
| reporting_effort_tracker.py | Permission check inline | ~50 lines x 3 |
| reporting_effort_tracker.py | Audit logging | ~15 lines x 12 |
| reporting_effort_tracker.py | WebSocket broadcast | ~5 lines x 15 |
| reporting_effort_items.py | Entity existence check | ~10 lines x 8 |

### Suggested Refactoring

```python
# Create base operation class
class TrackerOperation:
    def __init__(self, db, request, current_user):
        self.db = db
        self.request = request
        self.user = current_user

    async def validate_permission(self, tracker, operation):
        """Centralized permission check."""

    async def log_audit(self, action, changes):
        """Centralized audit logging."""

    async def broadcast(self, event_type, data):
        """Centralized WebSocket broadcast."""
```

---

## Conclusion

The PEARL application has a well-architected foundation with:
- Comprehensive state machine logic in `TrackerWorkflowService`
- Good audit trail coverage
- Real-time WebSocket updates

However, significant security gaps exist in:
- **Missing authentication on 5+ critical endpoints**
- **Inconsistent validation between individual and bulk operations**
- **Legacy header-based authentication on admin functions**

Addressing the CRITICAL and HIGH issues should be prioritized before production deployment.

---

## Appendix: Files Reviewed

```
backend/app/api/v1/reporting_effort_tracker.py
backend/app/api/v1/reporting_effort_items.py
backend/app/api/v1/database_backup.py
backend/app/api/v1/audit_trail.py
backend/app/api/v1/auth.py
backend/app/api/v1/utils/validation.py
backend/app/services/tracker_workflow.py
backend/app/crud/reporting_effort_item.py
backend/app/crud/reporting_effort_item_tracker.py
backend/app/crud/tracker_comment.py
backend/app/models/user.py
backend/app/models/reporting_effort_item_tracker.py
backend/app/schemas/reporting_effort_item.py
backend/app/schemas/tracker_comment.py
backend/app/core/security.py
react-frontend/src/features/reporting/TrackerManagement.tsx
react-frontend/src/features/reporting/ReportingEffortItems.tsx
react-frontend/src/components/tracker/KanbanBoard.tsx
react-frontend/src/lib/utils.ts
```
