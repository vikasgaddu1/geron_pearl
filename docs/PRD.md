## PEARL — Product Requirements Document (Unified Frontend + Backend)

This single PRD contains separate sections for the Backend (FastAPI) and the Admin Frontend (R Shiny) so they can be referenced independently.

### Backend — Product Requirements

Version: 1.0 • Date: 2025-08-07

### 1. Overview
PEARL is a full-stack research data management system. The backend is a FastAPI service using async PostgreSQL with SQLAlchemy 2.0, Pydantic v2, and Alembic, providing CRUD APIs and real-time WebSocket updates. It integrates with an R Shiny admin frontend.

### 2. Goals
- Provide reliable CRUD APIs for core entities: Study, DatabaseRelease, ReportingEffort, TextElement, Package, and PackageItem.
- Ensure strong data integrity via duplicate prevention and deletion protection.
- Expose real-time WebSocket broadcasts for UI synchronization.
- Offer clear OpenAPI docs and health checks for operations.

### 3. Non-Goals
- End-user analytics/visualization (handled in frontend).
- Full authentication/authorization rollout (placeholders exist; production hardening deferred).
- Batch test reliability across DB (documented constraint—use individual tests).

### 4. Users and Personas
- Admin Data Manager: curates studies, releases, reporting efforts, text content, and packages.
- Analyst/Scientist: consumes curated data structures for reporting and research outputs.
- System Operator: deploys, monitors health, manages DB migrations.

### 5. Scope and Functional Requirements

5.1 Health API
- Endpoint: GET /health
- Must verify database connectivity and return healthy/unhealthy status with details.

5.2 Studies
- Endpoints: /api/v1/studies (POST, GET list), /api/v1/studies/{id} (GET, PUT, DELETE)
- Must enforce unique study_label.
- Must block deletion when DatabaseRelease records exist; return HTTP 400 with descriptive message.
- Must broadcast study_created, study_updated, study_deleted over WebSocket.

5.3 Database Releases
- Endpoints: /api/v1/database-releases (POST, GET list with optional study_id), /api/v1/database-releases/{id} (GET, PUT, DELETE)
- Must require existing Study.
- Must enforce uniqueness of database_release_label within a Study.
- Must block deletion when ReportingEffort records exist; HTTP 400 with descriptive message.
- Must broadcast database_release_* events over WebSocket.

5.4 Reporting Efforts
- Endpoints: /api/v1/reporting-efforts (POST, GET list with filters), /api/v1/reporting-efforts/{id} (GET, PUT, DELETE)
- Must require existing Study and DatabaseRelease and verify the release belongs to the Study.
- Must broadcast reporting_effort_* events over WebSocket.

5.5 Text Elements
- Endpoints: /api/v1/text-elements (POST, GET list), /api/v1/text-elements/search (GET), /api/v1/text-elements/{id} (GET, PUT, DELETE)
- Types: title, footnote, population_set, acronyms_set.
- Must prevent duplicates using case-insensitive, space-insensitive comparison; return HTTP 400 on conflict.
- Must provide search by label and optional type filter.
- Must broadcast text_element_* events over WebSocket.

5.6 Packages and Package Items
- Endpoints:
  - Packages: /api/v1/packages (POST, GET list), /api/v1/packages/{id} (GET with items, PUT, DELETE)
  - Items: /api/v1/packages/{package_id}/items (POST, GET), /api/v1/packages/items/{item_id} (GET, PUT, DELETE)
- Package must have unique package_name.
- Package deletion must be blocked if items exist; respond with item codes in the error message (first 5).
- PackageItem must be unique on (package_id, item_type, item_subtype, item_code).
- Item creation must support details (TLF or Dataset) and associations (footnotes, acronyms) in one transaction.
- Must broadcast package_* and package_item_* events over WebSocket.

5.7 WebSocket Real-time Updates
- Endpoint: /api/v1/ws/studies (WebSocket upgrade path).
- Must send initial snapshot and support client actions: refresh, ping.
- Must broadcast entity events with serialized JSON (including Enum handling) and clean up stale connections.

### 6. API Contracts (Summary)
- Health: GET /health → 200 healthy or 503 unhealthy.
- Studies: POST/GET/GET by id/PUT/DELETE at /api/v1/studies[/{id}].
- Database Releases: POST/GET (optional study_id)/GET by id/PUT/DELETE at /api/v1/database-releases[/{id}].
- Reporting Efforts: POST/GET (filters study_id, database_release_id)/GET by id/PUT/DELETE.
- Text Elements: POST/GET/search/GET by id/PUT/DELETE at /api/v1/text-elements[...].
- Packages: POST/GET/GET by id (with items)/PUT/DELETE at /api/v1/packages[/{id}].
- Package Items: POST/GET at /api/v1/packages/{package_id}/items; GET/PUT/DELETE at /api/v1/packages/items/{item_id}.
- OpenAPI available at /docs and /redoc.

### 7. Data Model (Overview)
- Study (root) 1–N DatabaseRelease 1–N ReportingEffort.
- TextElement (independent) typed enum with timestamps.
- Package: container of PackageItem entries.
- PackageItem: polymorphic with TLF and Dataset details; many-to-many with TextElement via footnotes/acronyms junctions.
- Constraints:
  - Study.study_label unique.
  - DatabaseRelease.database_release_label unique per Study.
  - Package.package_name unique.
  - PackageItem unique composite key (package_id, item_type, item_subtype, item_code).

### 8. Non-Functional Requirements
- Performance: Support pagination (skip/limit); efficient relationship loading (selectinload where applicable).
- Reliability: Startup initializes DB; global exception handler returns structured errors.
- Security: CORS configured; JWT/API key placeholders present—production secrets required.
- Observability: Logging for CRUD/WebSocket broadcasts and connection lifecycle.
- Documentation: Auto-generated docs at /docs and /redoc; backend README kept current.

### 9. Testing Strategy and Constraints
- Individual test execution only for DB-backed tests due to async session conflicts; batch failures are expected.
- Prefer validator tests and single-operation DB tests.
- Model validation tool required after schema/model changes: backend/tests/validator/.

### 10. Success Metrics
- CRUD endpoints return correct HTTP codes and enforce constraints.
- WebSocket broadcasts reach connected clients with accurate payloads.
- Deletion protection prevents integrity violations with descriptive errors.
- Duplicate-prevention logic blocks near-duplicates for Text Elements and names for Studies/Packages.

### 11. Dependencies
- Python 3.11+, FastAPI, SQLAlchemy 2 (async) + asyncpg, Pydantic v2, Alembic, Uvicorn, UV, PostgreSQL.
- Frontend: R Shiny (bslib, shinyvalidate) consuming the API and WebSocket.

### 12. Risks and Mitigations
- Async DB session conflicts in batch tests → Run tests individually; document and enforce patterns.
- WebSocket client state divergence → Initial data snapshot + refresh action + stale connection cleanup.
- Enum serialization issues → Ensure conversion via sqlalchemy_to_dict and JSON serializer for Enums.

### 13. Rollout Plan
1) Database migrations applied (alembic upgrade head). 2) Initialize DB on startup. 3) Deploy backend (Uvicorn). 4) Configure CORS and secrets. 5) Start Shiny frontend and validate CRUD + WebSocket flows.

### 14. Open Questions
- Authentication/authorization scope and roles? Timeline for JWT enablement.
- Search and indexing strategy for TextElement at scale.
- Pagination defaults and maximums per entity (finalize API contract values).

### 15. References
- Code: backend/app/api/v1/*.py, backend/app/crud/*.py, backend/app/models/*.py, backend/app/schemas/*.py
- Docs: backend/README.md, backend/CLAUDE.md, root CLAUDE.md
- Testing: backend/tests/README.md, backend/tests/validator/


### Frontend (Admin R Shiny) — Product Requirements

Version: 1.0 • Date: 2025-08-07

#### 1. Overview
Admin dashboard built with R Shiny providing CRUD UI over the backend APIs with real-time WebSocket updates. Uses bslib for Bootstrap 5 theming and shinyvalidate for form validation. Multi-user sessions stay in sync via WebSocket broadcasts.

#### 2. Goals
- Modern, responsive UI for managing Studies, Database Releases, Reporting Efforts, and Text Elements (TNFP).
- Real-time synchronization across sessions using WebSocket client.
- Robust validation, error handling, and status indicators.

#### 3. Non-Goals
- Complex analytics dashboards (future scope).
- Offline mode; app assumes reachable backend API.

#### 4. Users and Personas
- Admin Data Manager: Maintains entities via UI.
- Analyst: Verifies data completeness and status.

#### 5. Scope and Functional Requirements
- Studies Management
  - List, create, edit, delete via REST: GET/POST/PUT/DELETE /api/v1/studies[…].
  - Respect backend duplicate and deletion-protection rules with clear client messages.
- Database Releases
  - CRUD bound to selected Study; enforce constraints from backend responses.
- Reporting Efforts
  - CRUD bound to Study and Database Release; verify cross-entity constraints.
- TNFP (Text Elements)
  - Unified management of types: title, footnote, population_set, acronyms_set.
  - Duplicate-prevention UX: show detailed backend error and guidance; normalize preview hints (space/case-insensitive).
- **Packages Management (NEW - Added 2025-08-07)**
  - **Package CRUD Operations**:
    - List all packages with creation timestamps in sortable/searchable table
    - Create new packages with unique name validation (minimum 3 characters)
    - Delete packages (blocked if package items exist - shows first 5 item codes in error)
    - Edit package names (UI buttons present, backend ready, implementation pending)
  - **Package Items Management**:
    - Two-tab interface: "Packages" tab for package management, "Package Items" tab for items
    - Package selector dropdown to switch between packages
    - Support for two item types: TLF (Tables/Listings/Figures) and Dataset (SDTM/ADaM)
    - TLF items require: study, subtype (Table/Listing/Figure), and TLF ID code
    - Dataset items require: study, subtype (SDTM/ADaM), dataset name, and optional label
    - Each item displays associated study label fetched from backend
    - Delete individual items with confirmation modal
    - Unique constraint: (package_id, item_type, item_subtype, item_code) must be unique
  - **Real-time WebSocket Events**:
    - package_created, package_updated, package_deleted for package operations
    - package_item_created, package_item_updated, package_item_deleted for item operations
    - All events broadcast to synchronized sessions immediately
  - **Validation Rules**:
    - Package names must be unique across system
    - Package deletion blocked if any items exist (referential integrity)
    - Item creation requires valid study_id (verified against studies table)
    - Item type/subtype combinations validated (TLF→Table/Listing/Figure, Dataset→SDTM/ADaM)
  - **UI Components**:
    - Located in "Package Registry" navigation section
    - Sliding sidebar form for new package creation
    - Modal dialog for adding package items with conditional fields based on type
    - Action buttons (edit/delete) on each table row
    - Refresh button to manually reload data
- Health Monitoring
  - Surface /health status in UI; show connected/disconnected indicators.
- WebSocket Real-time Updates
  - Endpoint: ws://{API_HOST}/api/v1/ws/studies.
  - Handle events: study_created/updated/deleted, studies_update, database_release_*, reporting_effort_*, text_element_*, **package_*, package_item_***.
  - Auto-reconnect with exponential backoff; 30s ping/pong keep-alive.
- Environment Configuration
  - All endpoints configurable via env vars (e.g., PEARL_API_URL, PEARL_API_WEBSOCKET_PATH).
  - Module source order: `websocket_client.R` then `api_client.R` then UI/server modules.

#### 6. UI/UX Requirements
- bslib + Bootstrap 5 theme, responsive layouts; consistent card sizing (max-width 1200px, height ~700px), sidebar ~450px.
- DT-based tables with search/filter/pagination; action buttons for edit/delete.
- Valid Shiny notification types only: default, message, warning, error.
- Clear connection status indicators (🟢 Connected / 🔴 Disconnected / Reconnecting).

#### 7. Validation and Error Handling
- Use shinyvalidate for all form inputs with immediate feedback.
- Parse backend 400 errors for duplicate-prevention; present detailed guidance.
- Graceful degradation when WebSocket unavailable (optional HTTP refresh fallback).

#### 8. API Integration
- HTTP via httr/httr2; centralized in `modules/api_client.R`.
- Consistent endpoint formation (collection routes use trailing slash as required by backend).
- Standard JSON parsing; user-friendly error messages from HTTP status codes.

#### 9. Non-Functional Requirements
- Performance: Efficient table rendering; avoid blocking UI during network calls.
- Reliability: Auto-reconnect WebSocket; retry logic for transient HTTP failures.
- Maintainability: Modular UI/server pattern; environment-driven configuration; renv for reproducible packages.

#### 10. Dependencies
- R 4.3+, shiny, bslib, bsicons, shinyWidgets, DT, httr/httr2, jsonlite, websocket, later, dplyr, lubridate, shinyvalidate, renv.

#### 11. Testing
- Manual verification of CRUD flows and WebSocket sync across multiple browser sessions.
- Backend integration tests: run `uv run python tests/integration/test_websocket_broadcast.py` while observing UI.
- Health check via curl to /health reflected in UI.

#### 12. Risks and Mitigations
- WebSocket message format drift → Keep `www/websocket_client.js` routing aligned with backend event types.
- Env var misconfiguration → Centralized load, early validation, and clear error banners.
- Large tables responsiveness → Use pagination and server-side filtering where needed.

#### 13. Rollout
1) Back end running at configured URL. 2) `renv::restore()` to install dependencies. 3) `Rscript run_app.R` to start on port 3838. 4) Verify CRUD + real-time updates.

#### 14. References
- Docs: admin-frontend/README.md, admin-frontend/CLAUDE.md
- Code: admin-frontend/app.R, modules/*.R, www/websocket_client.js

### TestSprite Testing Guidelines for Packages Feature

#### Test Environment Setup
1. **Backend**: Ensure FastAPI backend is running on http://localhost:8000
2. **Frontend**: R Shiny app running on http://localhost:3838
3. **Database**: PostgreSQL with packages tables migrated
4. **Test Data**: Use provided test script `/test_packages_frontend.sh` to create sample data

#### Test Scenarios for Packages Feature

##### 1. Package CRUD Operations
**Test Case P1: Create Package**
- Navigate to "Package Registry" tab in sidebar
- Click "Add Package" button
- Enter package name (min 3 chars)
- Verify success notification
- Verify package appears in table
- Test duplicate name rejection

**Test Case P2: Delete Package (Empty)**
- Create a test package
- Click delete button (trash icon)
- Confirm deletion in modal
- Verify package removed from table

**Test Case P3: Delete Package (With Items - Should Fail)**
- Create package with items
- Attempt deletion
- Verify error message shows item codes
- Verify package NOT deleted

##### 2. Package Items Management
**Test Case PI1: Add TLF Item**
- Select "Package Items" tab
- Choose package from dropdown
- Click "Add Item"
- Select Study, Type=TLF, Subtype=Table
- Enter TLF ID (e.g., T14.1.1)
- Verify item appears in table with study label

**Test Case PI2: Add Dataset Item**
- Select package from dropdown
- Click "Add Item"
- Select Study, Type=Dataset, Subtype=ADaM
- Enter dataset name (e.g., ADSL)
- Enter optional label
- Verify item appears correctly

**Test Case PI3: Delete Item**
- Select package with items
- Click delete on any item
- Confirm in modal
- Verify item removed
- Verify package can now be deleted if last item

##### 3. Real-time WebSocket Synchronization
**Test Case WS1: Multi-Session Package Updates**
- Open app in two browser tabs/windows
- Create package in Tab 1
- Verify appears immediately in Tab 2
- Add item in Tab 2
- Verify appears in Tab 1

**Test Case WS2: Cross-Module Updates**
- Create/modify study in Studies tab
- Navigate to Packages → Package Items
- Verify new study available in dropdown

##### 4. Validation and Error Handling
**Test Case V1: Package Name Validation**
- Try empty name → should show error
- Try <3 characters → should show error  
- Try duplicate name → should show error
- Try valid unique name → should succeed

**Test Case V2: Item Validation**
- Try creating item without study → error
- Try invalid type/subtype combo → error
- Try duplicate item code → error

**Test Case V3: Referential Integrity**
- Delete study used in package items → should fail
- Error should list dependent packages

##### 5. UI/UX Consistency
**Test Case UX1: Interface Elements**
- Verify tab navigation works
- Verify dropdown updates after package creation
- Verify table search/filter/pagination
- Verify modal forms display correctly
- Verify all buttons have proper icons

**Test Case UX2: Responsive Design**
- Test at different screen sizes
- Verify sidebar collapses properly
- Verify tables remain usable on smaller screens

#### Expected WebSocket Events
Monitor browser console (F12) for these events:
- `📦 PACKAGE EVENT RECEIVED: package_created`
- `📦 PACKAGE EVENT RECEIVED: package_updated`
- `📦 PACKAGE EVENT RECEIVED: package_deleted`
- `📦 PACKAGE ITEM EVENT RECEIVED: package_item_created`
- `📦 PACKAGE ITEM EVENT RECEIVED: package_item_deleted`

#### API Endpoints to Verify
- `GET /api/v1/packages/` - List packages
- `POST /api/v1/packages/` - Create package
- `DELETE /api/v1/packages/{id}` - Delete package
- `GET /api/v1/packages/{id}/items` - Get package items
- `POST /api/v1/packages/{id}/items` - Create item
- `DELETE /api/v1/packages/items/{id}` - Delete item

#### Known Limitations to Note
1. Edit functionality for packages not yet implemented (buttons present but inactive)
2. No bulk operations support
3. No export/import functionality
4. Package items cannot be moved between packages

#### Test Data Creation Script
```bash
# Run from project root
chmod +x test_packages_frontend.sh
./test_packages_frontend.sh
```

This creates:
- 1 test package
- 1 test study (if none exist)
- 1 TLF item (Table type)
- 1 Dataset item (ADaM type)

#### Success Criteria
- All CRUD operations function correctly
- WebSocket updates occur within 1 second
- Validation messages are clear and helpful
- No console errors during normal operation
- UI remains responsive during operations
- Multi-session synchronization works reliably

