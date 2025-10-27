## Role-Based Access Plan (Phase 2)

Last updated: 2025-08-20

### Goal
Implement clear, enforceable role-based access control (RBAC) across the PEARL system while continuing to use the single `admin-frontend` Shiny app. Provide two dashboards (Admin vs. Editor/Viewer) and restrict API/UI capabilities per role.

### Roles
- ADMIN: Full access to the app and all APIs
- EDITOR: Full access to Reporting Effort Tracker forms (create/update/assign/unassign) but cannot delete trackers and has no access to other app features
- VIEWER: Read-only access; can view and search tracker items across all Reporting Efforts

### Capability Matrix (High-Level)
- VIEWER
  - Tracker: read-only across all Reporting Efforts; global search and filters
  - No create/update/delete; no import/export; no user/database/admin features
- EDITOR
  - All VIEWER capabilities
  - Tracker form: create, edit, assign/unassign programmers, update statuses/fields; no delete
  - No import/export; no user/database/admin features
- ADMIN
  - Full app access (all modules: Studies, Packages, TNFP, Users, Database Backup, Audit Trail, Trackers, etc.)
  - All tracker operations including delete and bulk operations

---

## Backend Changes (FastAPI)

### 1) Centralized Role Extraction and Enforcement
- Add a reusable dependency to extract role from request headers (temporary approach) and enforce allowed roles per endpoint.
  - Source: `backend/app/core/security.py` (or new `backend/app/api/v1/utils/roles.py`)
  - Function: `require_roles(allowed: set[str]) -> Callable`
  - Implementation idea:
    - Extract role from header `X-User-Role` (string) for now
    - Normalize into `UserRole` enum (ADMIN/EDITOR/VIEWER)
    - If role not in `allowed`, raise 403
  - Note: This is an interim solution. Long-term, replace headers with real auth (JWT/session) and map to DB users.

### 2) Apply RBAC to Tracker Endpoints
File: `backend/app/api/v1/reporting_effort_tracker.py`
- GET `/` + filters: allowed {ADMIN, EDITOR, VIEWER}
- GET `/{tracker_id}`: allowed {ADMIN, EDITOR, VIEWER}
- GET `/by-item/{item_id}`: allowed {ADMIN, EDITOR, VIEWER}
- GET `/by-programmer/{programmer_id}`: allowed {ADMIN, EDITOR}
- POST `/` (create): allowed {ADMIN, EDITOR}
- PUT `/{tracker_id}` (update): allowed {ADMIN, EDITOR}
- DELETE `/{tracker_id}` (delete): allowed {ADMIN}
- POST `/{tracker_id}/assign-programmer`: allowed {ADMIN, EDITOR}
- DELETE `/{tracker_id}/unassign-programmer`: allowed {ADMIN, EDITOR}
- POST `/bulk-assign`: allowed {ADMIN}
- POST `/bulk-status-update`: allowed {ADMIN}
- GET `/workload-summary`: allowed {ADMIN, EDITOR}
- GET `/workload/{programmer_id}`: allowed {ADMIN, EDITOR}
- GET `/export/{reporting_effort_id}`: allowed {ADMIN}
- POST `/import/{reporting_effort_id}`: allowed {ADMIN}

Notes:
- Editor can do everything on the tracker form except deletion.
- Viewer can read/search across all RE.

### 3) Apply/Confirm RBAC on Other Admin APIs
- `audit_trail.py`: already using `X-User-Role=admin`. Replace with `require_roles({ADMIN})`.
- `database_backup.py`: already admin-only. Replace with `require_roles({ADMIN})`.
- `users.py`: all endpoints admin-only. Add `require_roles({ADMIN})`.
- `packages.py`, `studies.py`, etc.: Admin-only for create/update/delete; read endpoints may remain open to Admin only (current admin-frontend only).

### 4) Broadcasts and Events
- WebSocket broadcasts remain unchanged. The server-side RBAC ensures only allowed mutations occur.

### 5) Testing (Backend)
- Add tests in `backend/tests`:
  - Viewer: 200 for GET trackers; 403 for POST/PUT/DELETE
  - Editor: 200 for POST/PUT; 403 for DELETE/import/export/bulk
  - Admin: 200 for all; ensure deletes succeed
  - Include `X-User-Role` header in requests

---

## Frontend Changes (admin-frontend Shiny)

We will continue using the single `admin-frontend` app, with role-based UI gating and API headers.

### 1) Current User and Role Context
- Add a minimal role context in `app.R` using environment variables (dev) and a future hook for real auth:
  - Env vars: `PEARL_DEV_MODE`, `PEARL_DEV_USER_ID`, `PEARL_DEV_USERNAME`, `PEARL_DEV_ROLE` (ADMIN/EDITOR/VIEWER)
  - Default role for dev: `ADMIN`
  - Expose helpers via `modules/utils/api_utils.R`:
    - `get_current_role()` returns string role
    - `with_role_header(req)` adds `X-User-Role = get_current_role()` to httr2 requests
- Update all API calls in `modules/api_client.R` to pass role header via `with_role_header()` (especially tracker endpoints). Keep admin-only headers for backup/audit (now unified via helper).

### 2) UI Gating (Show/Hide Navigation and Actions)
- In `app.R`, decide nav visibility based on `current_role` at app startup:
  - Admin-only nav: `User Management`, `Database Backup`, `Admin Dashboard` (full)
  - Editor/Viewer nav: only `Reporting Effort Tracker` and the new Editor/Viewer Dashboard
  - Optionally leave read-only access to `Reporting Effort Items` list for Editor/Viewer (view-only), but default to hiding for simplicity per requirements
- In `modules/reporting_effort_tracker_server.R`:
  - Hide or disable Delete buttons if role != ADMIN (do not render delete action cell or bind handler)
  - Ensure all edit modal form fields remain available for EDITOR and ADMIN; make them read-only for VIEWER
  - Respect RBAC errors from API and surface as notifications

### 3) Two Dashboards
- Keep existing Admin Dashboard:
  - Files: `modules/admin_dashboard_ui.R`, `modules/admin_dashboard_server.R`
  - Visible only to ADMIN
- Add new Editor/Viewer Dashboard:
  - Files: `modules/editor_viewer_dashboard_ui.R`, `modules/editor_viewer_dashboard_server.R`
  - Focus: Reporting Effort progress and workload visibility; global search across trackers
  - Features:
    - KPI tiles: total trackers, by production status, by QC status
    - Filters: Reporting Effort, production programmer, QC programmer, statuses, priority, due date ranges
    - Search: free-text across item code/name/comments summary
    - Table: track key fields (item_code, title/label, production_programmer, qc_programmer, production_status, qc_status, due_date, qc_completion_date, priority, qc_level)
    - Actions:
      - VIEWER: open read-only modal
      - EDITOR: open full edit modal (no delete)
    - Real-time updates via existing WebSocket handlers (table refresh or surgical updates)

### 4) Tracker Form Permissions
- Fields editable for EDITOR and ADMIN:
  - production_programmer_id (username lookup), qc_programmer_id
  - production_status, qc_status
  - in_production_flag, priority, qc_level
  - due_date, qc_completion_date
- READ-ONLY for VIEWER
- DELETE action only visible to ADMIN

### 5) Minimal Code Touch Points
- `admin-frontend/app.R`: compute `current_role`; build navbar conditionally; wire dashboard module selection
- `admin-frontend/modules/utils/api_utils.R`: add role helpers and httr2 request wrapper
- `admin-frontend/modules/api_client.R`: wrap all requests with `with_role_header()`
- `admin-frontend/modules/reporting_effort_tracker_server.R`: conditional rendering of actions (hide delete), read-only mode for VIEWER
- New modules: `editor_viewer_dashboard_ui.R` and `_server.R`

### 6) Testing (Frontend)
- Playwright tests (extend `tests/console-errors.spec.ts` or add new files):
  - As VIEWER: no delete/edit buttons; search works; opening tracker shows read-only fields
  - As EDITOR: edit buttons present; delete buttons absent; PUT succeeds; DELETE blocked server-side if attempted manually
  - As ADMIN: all actions present; delete works
  - Use environment variable `PEARL_DEV_ROLE` to simulate roles in CI

---

## Implementation Steps (Sequenced)
1) Backend: introduce `require_roles` dependency and wire into audit, backup, users, tracker endpoints
2) Backend: add unit/integration tests for role enforcement
3) Frontend: `api_utils.R` role helpers and request wrapper
4) Frontend: apply header wrapper across `api_client.R` (tracker endpoints first)
5) Frontend: update `reporting_effort_tracker_server.R` to hide delete for non-admin; make form read-only for VIEWER
6) Frontend: add `editor_viewer_dashboard_ui.R` and `_server.R`; add to navbar conditionally in `app.R`
7) Frontend: adjust `app.R` nav visibility by role; keep existing Admin Dashboard for ADMIN
8) Frontend tests: Playwright specs for role-specific UI
9) Docs: update `docs/PRD.md` (RBAC section) to reflect finalized roles

---

## Acceptance Criteria
- Viewer can load the app, access the Editor/Viewer Dashboard, see/search all trackers, and cannot see any edit/delete controls
- Editor can open the same dashboard, edit tracker fields (no delete), and is blocked server-side from deletions/import/export/bulk
- Admin can access full Admin Dashboard and all modules; all tracker operations are available
- API returns 403 when a disallowed role performs restricted actions
- Playwright tests pass for all three roles in CI

---

## Configuration
- Environment variables (frontend):
  - `PEARL_DEV_MODE=true|false`
  - `PEARL_DEV_USER_ID=<int>`
  - `PEARL_DEV_USERNAME=<string>`
  - `PEARL_DEV_ROLE=ADMIN|EDITOR|VIEWER`
- Header used for interim backend RBAC: `X-User-Role`

---

## Open Questions / Follow-ups
- Authentication: plan to replace header-based role with JWT/session-backed auth; define login in a future phase
- Fine-grained read filters: should Viewer see everything or only assigned? Requirement states “see trackers for all RE,” so scope is global for now
- Import/Export permissions: kept Admin-only; confirm if Editor needs export-only in a later phase
- Non-tracker read-only modules: we currently hide them for Editor/Viewer; confirm if any read-only access is desired later




