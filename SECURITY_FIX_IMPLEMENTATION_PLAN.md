# Security Fix Implementation Plan

**Branch**: `security/fix-authentication-and-permissions`
**Created**: January 5, 2026
**Status**: In Progress

---

## Phase 1: Fix CRITICAL Missing Authentication (5 Endpoints)

### 1.1 Bulk TLF Upload - Add Authentication
**File**: `backend/app/api/v1/reporting_effort_items.py:660`
**Endpoint**: `POST /api/v1/reporting-effort-items/{reporting_effort_id}/bulk-tlf`

**Changes**:
- Add `current_user: UserModel = Depends(get_current_user)` parameter
- Add admin role check: `if current_user.role != UserRole.ADMIN: raise HTTPException(403)`

### 1.2 Bulk Dataset Upload - Add Authentication
**File**: `backend/app/api/v1/reporting_effort_items.py:846`
**Endpoint**: `POST /api/v1/reporting-effort-items/{reporting_effort_id}/bulk-dataset`

**Changes**: Same as 1.1

### 1.3 Import Trackers - Add Authentication
**File**: `backend/app/api/v1/reporting_effort_tracker.py:1363`
**Endpoint**: `POST /api/v1/reporting-effort-tracker/import/{reporting_effort_id}`

**Changes**:
- Add `current_user: UserModel = Depends(get_current_user)` parameter
- Add admin role check
- Update audit logging to use `current_user.id` instead of header

### 1.4 Unassign Programmer - Add Authentication
**File**: `backend/app/api/v1/reporting_effort_tracker.py:678`
**Endpoint**: `DELETE /api/v1/reporting-effort-tracker/{tracker_id}/unassign-programmer`

**Changes**:
- Add `current_user: UserModel = Depends(get_current_user)` parameter
- Add admin role check (only admin can unassign)

### 1.5 Delete Tracker - Add Authentication
**File**: `backend/app/api/v1/reporting_effort_tracker.py:470`
**Endpoint**: `DELETE /api/v1/reporting-effort-tracker/{tracker_id}`

**Changes**:
- Add `current_user: UserModel = Depends(get_current_user)` parameter
- Add admin role check

---

## Phase 2: Fix HIGH Priority Permission Issues (7 Items)

### 2.1 Reporting Effort Item Update - Add Permission Check
**File**: `backend/app/api/v1/reporting_effort_items.py:485`
**Endpoint**: `PUT /api/v1/reporting-effort-items/{item_id}`

**Changes**:
- Add `current_user: UserModel = Depends(get_current_user)` parameter
- VIEWER cannot update, EDITOR can update, ADMIN can update

### 2.2 Copy from Package - Add Permission Check
**File**: `backend/app/api/v1/reporting_effort_items.py:975`
**Endpoint**: `POST /api/v1/reporting-effort-items/{reporting_effort_id}/copy-from-package`

**Changes**:
- Add authentication (admin only for bulk operations)

### 2.3 Copy from Reporting Effort - Add Permission Check
**File**: `backend/app/api/v1/reporting_effort_items.py:1286`
**Endpoint**: `POST /api/v1/reporting-effort-items/{reporting_effort_id}/copy-from-reporting-effort`

**Changes**:
- Add authentication (admin only for bulk operations)

### 2.4-2.5 Already Fixed (Bulk operations have admin check)

---

## Phase 3: Add Validation Consistency to Bulk Operations

### 3.1 Bulk Status Update - Add Business Rules
**File**: `backend/app/api/v1/reporting_effort_tracker.py:888`
**Endpoint**: `POST /api/v1/reporting-effort-tracker/bulk-status-update`

**Changes**:
- Add unresolved comment check before QC=completed
- Apply `TrackerWorkflowService.apply_status_transition()` for each tracker

### 3.2 Bulk Assign-Status - Add Auto-Transitions
**File**: `backend/app/api/v1/reporting_effort_tracker.py:960`
**Endpoint**: `POST /api/v1/reporting-effort-tracker/bulk-assign-status`

**Changes**:
- Add unresolved comment check
- Apply auto-transitions via TrackerWorkflowService

---

## Phase 4: Replace Legacy Header-Based Auth

### 4.1 Database Backup - Switch to JWT
**File**: `backend/app/api/v1/database_backup.py`

**Changes**:
- Replace `check_admin_access()` with `require_role([UserRole.ADMIN])`
- Update all endpoints to use JWT authentication

### 4.2 Audit Trail - Switch to JWT
**File**: `backend/app/api/v1/audit_trail.py`

**Changes**:
- Replace header-based check with JWT dependency

---

## Phase 5: Create Centralized PermissionService

### 5.1 Create Permission Service
**File**: `backend/app/services/permission_service.py` (new)

```python
class PermissionService:
    @staticmethod
    def require_admin(user: User) -> None:
        """Raise 403 if user is not admin."""

    @staticmethod
    def require_editor_or_admin(user: User) -> None:
        """Raise 403 if user is viewer."""

    @staticmethod
    def check_tracker_permission(user: User, tracker, operation: str) -> None:
        """Check if user can perform operation on tracker."""
```

---

## Phase 6: Verification

### 6.1 Run Backend Tests
```bash
cd backend && ./tests/scripts/test_crud_simple.sh
```

### 6.2 Manual API Testing
- Test each fixed endpoint with VIEWER/EDITOR/ADMIN roles
- Verify 403 responses for unauthorized access
- Verify audit logging captures correct user

### 6.3 Build Frontend
```bash
cd react-frontend && npm run build
```

---

## Phase 7: Merge to Main

```bash
git checkout main
git merge security/fix-authentication-and-permissions
git push
```

---

## Verification Checklist

- [ ] Bulk TLF upload requires admin
- [ ] Bulk dataset upload requires admin
- [ ] Import trackers requires admin
- [ ] Unassign programmer requires admin
- [ ] Delete tracker requires admin
- [ ] Item update requires editor or admin
- [ ] Copy operations require admin
- [ ] Bulk status update validates comments
- [ ] Bulk assign-status applies transitions
- [ ] Database backup uses JWT
- [ ] Audit trail uses JWT
- [ ] All tests pass
- [ ] No regression in existing functionality
