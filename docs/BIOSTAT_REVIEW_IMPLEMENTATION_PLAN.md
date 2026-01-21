# Biostat Review Workflow for TLF Items

## Overview

Add a new "Biostat Review" stage in the production workflow that applies **only to TLF items** (Tables, Listings, Figures). After QC marks an item as completed, TLF items enter biostat review where a biostatistician can pass or fail the output.

## Workflow Diagram

### Current Workflow (All Items)
```
Production: not_started → in_progress → ready_for_qc → completed (auto-set by QC)
                                ↑                           ↓
QC:         not_started → in_progress ←──── failed    completed
```

### New Workflow (TLF Items Only)
```
Production: not_started → in_progress → ready_for_qc → completed (auto)
                ↑               ↑                           ↓
                │               │                      QC: completed
                │               │                           ↓
                │               └── biostat failed ←── pending (auto)
                │                                           ↓
                └───────────────────────────────────── passed ✓
```

**Key Flow:**
1. QC marks item as `completed` → TLF items auto-transition to biostat `pending`
2. Biostat reviews and either **passes** (done!) or **fails** (with required comment)
3. On fail: production → `in_progress`, QC → `not_started`, full cycle repeats
4. `in_production_flag` only settable after biostat `passed` for TLF items

---

## Design Decisions (Confirmed)

| Decision | Choice |
|----------|--------|
| Biostat Reviewer | New study-scoped BIOSTAT role; each study has default biostat |
| Comment Handling | Production marks biostat comments as "addressed"; biostat verifies on re-review |
| In-Production Flag | Requires biostat `passed` for TLF items |
| Kanban View | Third "Biostat Kanban" tab (Pending → Passed columns) |
| Fail Cycle | Full cycle: production → QC → biostat review again |
| Biostat Statuses | Simple: `not_applicable`, `pending`, `passed`, `failed` |

---

## Permission Matrix

| Action | Admin | LEAD | BIOSTAT | EDITOR | VIEWER |
|--------|-------|------|---------|--------|--------|
| View Biostat Kanban | ✓ | ✓ | ✓ | ✓ (read-only) | ✓ (read-only) |
| Biostat Pass/Fail | ✓ | ✓ | ✓ (assigned only) | ✗ | ✗ |
| Assign Biostat Reviewer | ✓ | ✓ | ✗ | ✗ | ✗ |
| Set Default Biostat | ✓ | ✓ | ✗ | ✗ | ✗ |
| Add Biostat Comments | ✓ | ✓ | ✓ (assigned only) | ✗ | ✗ |
| Mark Biostat Comments Addressed | ✓ | ✓ | ✗ | ✓ (prod programmer) | ✗ |

**BIOSTAT Role Specifics:**
- Can see all study items (read access)
- Can only pass/fail items assigned to them
- Cannot change their own assignment (only LEAD/Admin)
- Cannot add comments to unassigned items

---

## Workflow Edge Cases

| Scenario | Behavior |
|----------|----------|
| Biostat passes, then tracker is edited | Edits blocked after biostat pass (production complete) |
| `in_production` unset after biostat pass | Allowed - doesn't reset biostat_status |
| QC re-opened after biostat pass | Block QC status change after biostat pass |
| Production completes on Dataset item | Biostat remains `not_applicable` |
| Default biostat removed from study | Null assignment + warning on auto-assign |
| Locked effort | Block all biostat actions (pass/fail/assign) |

---

## Implementation Plan

### Phase 1: Database Schema & Models

**1.1 Add BiostatStatus Enum** (`backend/app/models/reporting_effort_item_tracker.py`)
```python
class BiostatStatus(str, Enum):
    NOT_APPLICABLE = "not_applicable"  # Dataset items
    PENDING = "pending"                # Awaiting biostat review
    PASSED = "passed"                  # Biostat approved
    FAILED = "failed"                  # Rejected, needs rework
```

**1.2 Add Fields to ReportingEffortItemTracker**
- `biostat_status: str` (default: "not_applicable")
- `biostat_reviewer_id: Optional[int]` (FK to users.id)
- `biostat_review_date: Optional[date]`
- `unresolved_biostat_comment_count: int` (default: 0)

**1.3 Add BIOSTAT Role** (`backend/app/models/user_study_role.py`)
```python
class StudyRole(str, Enum):
    VIEWER = "VIEWER"
    EDITOR = "EDITOR"
    LEAD = "LEAD"
    BIOSTAT = "BIOSTAT"  # NEW
```

**1.4 Create StudyDefaultBiostat Table**
```python
class StudyDefaultBiostat(Base, TimestampMixin):
    __tablename__ = "study_default_biostats"
    id: int (PK)
    study_id: int (FK studies.id, CASCADE)
    user_id: int (FK users.id, CASCADE)
    is_active: bool (default True)
```

**1.5 Database Indexes**
```sql
CREATE INDEX idx_tracker_biostat_status ON reporting_effort_item_tracker(biostat_status);
CREATE INDEX idx_tracker_biostat_reviewer ON reporting_effort_item_tracker(biostat_reviewer_id);
CREATE INDEX idx_study_default_biostat ON study_default_biostats(study_id);
```

**1.6 Alembic Migration**
- Add columns to `reporting_effort_item_tracker` with indexes
- Create `study_default_biostats` table with index
- **Data migration logic:**
  - Items with `qc_status = 'completed'` AND `item_type = 'TLF'` AND `in_production_flag = true` → `biostat_status = 'passed'` (grandfathered)
  - Items with `qc_status = 'completed'` AND `item_type = 'TLF'` AND `in_production_flag = false` → `biostat_status = 'pending'`
  - All other items → `biostat_status = 'not_applicable'`
  - Do NOT auto-assign biostat reviewer in migration (leave null, assign on first access)

### Phase 2: Backend Workflow Logic

**2.1 Update TrackerWorkflowService** (`backend/app/services/tracker_workflow.py`)

Auto-transitions to add:
```python
# QC completed → biostat pending (TLF only)
if status_field == "qc_status" and new_status == "completed":
    if item.item_type == "TLF":
        updates["biostat_status"] = "pending"
        # Auto-assign study's default biostat
        updates["biostat_reviewer_id"] = await get_study_default_biostat_id(study_id)

# Biostat failed → reset production and QC
if status_field == "biostat_status" and new_status == "failed":
    updates["production_status"] = "in_progress"
    updates["qc_status"] = "not_started"
```

**2.2 Validation Rules**

| Endpoint | New Validation |
|----------|----------------|
| Update to `ready_for_qc` | Block if `unresolved_biostat_comment_count > 0` |
| Update to `biostat_status = passed` | Block if `unresolved_comment_count > 0` |
| Set `in_production_flag = true` | For TLF: require `biostat_status = passed` |
| Biostat fail action | Require failure comment (comment_type = "biostat") |

**2.3 Comment System Updates** (`backend/app/crud/tracker_comment.py`)
- Track `unresolved_biostat_comment_count` separately
- Increment on biostat comment create
- Decrement when production marks as resolved (addressed)
- Add `"biostat"` to `CommentType` enum if not already present

**2.4 Lock System Integration**
All biostat endpoints must check effort lock status:
```python
# In biostat pass/fail/assign endpoints
effort = await get_reporting_effort_for_tracker(db, tracker_id)
if effort.is_locked:
    raise HTTPException(400, f"Cannot modify: Reporting effort is locked since {effort.locked_at}")
```

**2.5 Audit Logging**
Log all biostat status changes to audit trail:
```python
await audit_log.log_action(
    db,
    table_name="reporting_effort_item_tracker",
    record_id=tracker.id,
    action="UPDATE",
    user_id=current_user.id,
    changes={
        "biostat_status": {"old": old_status, "new": new_status},
        "biostat_reviewer_id": reviewer_id
    },
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```
Also log: default biostat assignments for studies

### Phase 3: Backend API Endpoints

**3.1 New Biostat Endpoints** (`backend/app/api/v1/reporting_effort_tracker.py`)
```
POST /api/v1/reporting-effort-tracker/{id}/biostat-pass
POST /api/v1/reporting-effort-tracker/{id}/biostat-fail  # Requires comment
POST /api/v1/reporting-effort-tracker/{id}/assign-biostat
```

**3.2 Study Default Biostat Endpoints** (`backend/app/api/v1/studies.py`)
```
GET  /api/v1/studies/{id}/default-biostat
PUT  /api/v1/studies/{id}/default-biostat
GET  /api/v1/studies/{id}/biostat-users  # Users with BIOSTAT role
```

**3.3 Update Existing Endpoints**
All tracker update endpoints need biostat validation:
- `PUT /api/v1/reporting-effort-tracker/{id}`
- `POST /api/v1/reporting-effort-tracker/bulk-assign`
- `POST /api/v1/reporting-effort-tracker/bulk-status-update`
- `POST /api/v1/reporting-effort-tracker/bulk-assign-status`

**3.4 Update Import Endpoint** (`POST /api/v1/reporting-effort-tracker/import/{id}`)
- Set `biostat_status = 'not_applicable'` for Dataset items
- Set `biostat_status = 'not_applicable'` for TLF items (pending only after QC completes)
- Do not assign biostat_reviewer_id during import

**3.5 Bulk Biostat Endpoints** (optional, for LEADs reviewing multiple items)
```
POST /api/v1/reporting-effort-tracker/bulk-biostat-pass
  Body: { tracker_ids: [1, 2, 3] }
POST /api/v1/reporting-effort-tracker/bulk-biostat-fail
  Body: { tracker_ids: [1, 2, 3], comment: "Required failure reason" }
```

**3.6 Notification Events**
Add new notification types to `NotificationType` enum and create notifications:

| Event | Notification Type | Recipient |
|-------|------------------|-----------|
| Biostat reviewer assigned | `assignment_biostat` | Biostat reviewer |
| Biostat failed | `biostat_failed` | Production programmer, QC programmer |
| Biostat passed | `biostat_passed` | Production programmer (optional) |
| Biostat comment added | `comment_added` (existing) | Production programmer |

**3.7 WebSocket Events**
- `biostat_status_updated` - When biostat status changes
- `biostat_assigned` - When biostat reviewer assigned
- `notification_created` - For biostat notifications (existing)

### Phase 4: Frontend Types & API

**4.1 Update Types** (`react-frontend/src/types/index.ts`)
```typescript
export type BiostatStatus = 'not_applicable' | 'pending' | 'passed' | 'failed'
export type StudyRole = 'VIEWER' | 'EDITOR' | 'LEAD' | 'BIOSTAT'

export interface ReportingEffortItemTracker {
  // ... existing fields
  biostat_status?: BiostatStatus
  biostat_reviewer_id?: number
  biostat_reviewer?: User
  biostat_review_date?: string
  unresolved_biostat_comment_count?: number
}
```

**4.2 API Endpoints** (`react-frontend/src/api/endpoints/tracker.ts`)
```typescript
biostatPass: (trackerId: number) => api.post(`/tracker/${trackerId}/biostat-pass`)
biostatFail: (trackerId: number, comment: string) => api.post(`/tracker/${trackerId}/biostat-fail`, { comment })
assignBiostat: (trackerId: number, userId: number) => api.post(`/tracker/${trackerId}/assign-biostat`, { user_id: userId })
bulkBiostatPass: (trackerIds: number[]) => api.post(`/tracker/bulk-biostat-pass`, { tracker_ids: trackerIds })
bulkBiostatFail: (trackerIds: number[], comment: string) => api.post(`/tracker/bulk-biostat-fail`, { tracker_ids: trackerIds, comment })
```

**4.3 State Management Updates** (`react-frontend/src/stores/`)
- Update `trackerStore.ts` to handle biostat_status
- Add WebSocket handlers for `biostat_status_updated` event
- Add filter state for biostat kanban view
- Update local state optimistically on pass/fail actions

**4.4 Backend API Response Updates**
- Add eager loading of `biostat_reviewer` relationship in tracker queries
- Include `biostat_reviewer` object in list responses (like `production_programmer`, `qc_programmer`)
- Update `TrackerResponse` schema to include biostat fields

### Phase 5: Frontend Kanban & UI

**5.1 Biostat Kanban View** (`react-frontend/src/components/tracker/BiostatKanbanBoard.tsx`)
- New component showing only TLF items
- Columns: `Pending` | `Passed` (items move out after pass)
- Swimlanes by item_subtype (Table, Listing, Figure)

**5.2 TrackerManagement Updates** (`react-frontend/src/features/reporting/TrackerManagement.tsx`)
- Add fourth view mode: `'kanban-biostat'`
- Tab button: "Biostat Kanban"
- Filter to TLF items only in this view

**5.3 Kanban Column Config**
```typescript
const BIOSTAT_COLUMNS = [
  { status: 'pending', title: 'Pending Review', colorClass: 'bg-orange-200 text-orange-800' },
  { status: 'passed', title: 'Passed', colorClass: 'bg-green-200 text-green-800' },
]
```

**5.4 Tracker Card Updates** (`react-frontend/src/components/tracker/KanbanCard.tsx`)
- Show biostat status badge for TLF items
- Show biostat reviewer name
- Show unresolved biostat comment count badge

**5.5 Biostat Failure Dialog**
- Modal requiring comment when biostat clicks "Fail"
- Comment auto-created with `comment_type = "biostat"`

**5.6 DataTable View Updates** (`react-frontend/src/features/reporting/TrackerManagement.tsx`)
- Add `biostat_status` column to table
- Add `biostat_reviewer` column to table
- Add filter dropdown for biostat status
- Add sort by biostat_review_date
- Show biostat status as colored badge (orange=pending, green=passed, gray=N/A)

**5.7 Comment UI Updates**
- Show biostat comments with distinct styling (different background color)
- Add "Biostat Comment" label/badge
- Only production programmer can mark biostat comments as "addressed"

### Phase 6: Study Settings UI

**6.1 Default Biostat Assignment**
- Add section in Study Settings for default biostat
- Dropdown of users with BIOSTAT role on study
- Auto-populate when assigning BIOSTAT role to first user

**6.2 Role Assignment UI Updates**
- Add BIOSTAT option to role dropdown in study member management
- Show BIOSTAT users in separate section

### Phase 7: Testing & Documentation

**7.1 Curl Test Script** (`backend/tests/scripts/test_biostat_workflow.sh`)
- Test QC complete → biostat pending auto-transition
- Test biostat pass flow
- Test biostat fail → production rework cycle
- Test validation rules (blocked actions)
- Test permission checks
- Test lock system blocks biostat actions
- Test audit log entries created
- Test notifications sent

**7.2 Playwright E2E Tests** (using Playwright MCP)
```typescript
describe('Biostat Workflow E2E', () => {
  test('QC complete triggers biostat pending for TLF items')
  test('Biostat pass workflow')
  test('Biostat fail with required comment')
  test('Real-time updates across sessions') // Two browser contexts
  test('BIOSTAT role visibility and permissions')
  test('Locked effort blocks biostat actions')
  test('DataTable shows biostat columns')
  test('Comment addressed flow')
});
```
Key scenarios:
- Login as QC user, complete TLF item → verify appears in Biostat Kanban
- Login as BIOSTAT user, pass/fail items
- Verify failure dialog requires comment
- Two-browser WebSocket sync test
- Role-based UI visibility

**7.3 Update CLAUDE.md**
- Add biostat workflow documentation
- Update workflow diagrams
- Add BIOSTAT role to role system docs
- Add notification types
- Add WebSocket event types

---

## Files to Modify

### Backend (18 files)
| File | Changes |
|------|---------|
| `models/reporting_effort_item_tracker.py` | Add BiostatStatus enum, new fields, indexes |
| `models/user_study_role.py` | Add BIOSTAT to StudyRole enum |
| `models/study_default_biostat.py` | NEW: StudyDefaultBiostat model |
| `models/tracker_comment.py` | Add "biostat" to CommentType enum |
| `models/notification.py` | Add biostat notification types |
| `models/__init__.py` | Export new model |
| `schemas/reporting_effort_item_tracker.py` | Add biostat fields to schemas |
| `schemas/study.py` | Add default biostat schemas |
| `schemas/tracker_comment.py` | Update CommentType enum |
| `services/tracker_workflow.py` | Add biostat auto-transitions, lock checks |
| `api/v1/reporting_effort_tracker.py` | Add biostat endpoints, validation, audit logging |
| `api/v1/studies.py` | Add default biostat endpoints |
| `crud/tracker_comment.py` | Track biostat comment count separately |
| `crud/study_default_biostat.py` | NEW: CRUD for default biostat |
| `crud/notification.py` | Add biostat notification creation |
| `crud/audit_log.py` | Add biostat-specific logging helpers |
| `migrations/versions/add_biostat_review.py` | NEW: Migration with data migration logic |
| `tests/scripts/test_biostat_workflow.sh` | NEW: Curl-based test script |

### Frontend (12 files)
| File | Changes |
|------|---------|
| `types/index.ts` | Add BiostatStatus, update StudyRole, NotificationType |
| `api/endpoints/tracker.ts` | Add biostat API functions |
| `api/endpoints/studies.ts` | Add default biostat API |
| `stores/trackerStore.ts` | Add biostat state handling, WebSocket handlers |
| `components/tracker/BiostatKanbanBoard.tsx` | NEW: Biostat kanban |
| `components/tracker/KanbanCard.tsx` | Show biostat status/reviewer |
| `components/tracker/TrackerComments.tsx` | Biostat comment styling, addressed toggle |
| `features/reporting/TrackerManagement.tsx` | Add biostat kanban tab, DataTable columns |
| `features/studies/StudySettings.tsx` | Default biostat setting |
| `features/users/UserManagement.tsx` | BIOSTAT role option |
| `components/common/DataTable.tsx` | Biostat column definitions (if needed) |
| `tests/e2e/biostat-workflow.spec.ts` | NEW: Playwright E2E tests |

---

## Multi-Tenant Confirmation

- `study_default_biostats` table has tenant isolation via `study.tenant_id` relationship
- BIOSTAT role is scoped to tenant's studies only (via `user_study_roles`)
- RLS policies apply to all biostat queries (inherited from tracker queries)
- Biostat reviewer must have access to the same tenant as the study

---

## Verification Plan

### 1. Backend API Tests (curl-based: `test_biostat_workflow.sh`)

**Workflow Tests:**
- Create TLF item, complete QC → verify biostat pending
- Create Dataset item, complete QC → verify biostat remains not_applicable
- Call biostat-pass → verify status changes to passed
- Call biostat-fail → verify production/QC reset to in_progress/not_started

**Validation Tests:**
- Try ready_for_qc with unaddressed biostat comments → verify blocked
- Try in_production_flag without biostat pass (TLF) → verify blocked
- Try in_production_flag on Dataset → verify allowed
- Try biostat actions on locked effort → verify blocked

**Permission Tests:**
- BIOSTAT user can pass/fail assigned items
- BIOSTAT user cannot pass/fail unassigned items
- LEAD can reassign biostat reviewer
- EDITOR cannot perform biostat actions

**Audit & Notification Tests:**
- Verify audit log entries created for pass/fail/assign
- Verify notifications sent to correct users

### 2. Frontend Manual Tests

**Role Assignment:**
- Assign BIOSTAT role to user in study settings
- Set default biostat for study
- Verify BIOSTAT appears in role dropdown

**Kanban Tests:**
- Complete QC on TLF item → verify appears in Biostat Kanban
- Pass item → verify removed from Pending column
- Fail item → verify failure dialog, required comment
- Verify items return to Production Kanban after fail

**DataTable Tests:**
- Verify biostat_status column shows
- Verify biostat_reviewer column shows
- Filter by biostat status works
- Sort by biostat_review_date works

**Comment Tests:**
- Biostat comments show distinct styling
- Production programmer can mark as addressed
- Cannot ready_for_qc with unaddressed comments

### 3. Playwright E2E Tests

**Core Workflow:**
- QC complete → biostat pending auto-transition
- Biostat pass workflow end-to-end
- Biostat fail with required comment

**Real-time:**
- Two browser contexts, WebSocket sync on pass/fail
- Notification appears in second browser

**Permissions:**
- BIOSTAT user sees Biostat Kanban tab
- VIEWER cannot perform biostat actions
- Locked effort blocks UI actions

---

## Future Enhancements (Out of Scope)

- **Analytics Dashboard**: Biostat metrics (pending count, pass/fail rates, avg review time)
- **Biostat Workload View**: Dashboard showing assigned items by reviewer
- **Auto-assignment Rules**: Round-robin or load-balanced biostat assignment
