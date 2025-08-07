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
- Health Monitoring
  - Surface /health status in UI; show connected/disconnected indicators.
- WebSocket Real-time Updates
  - Endpoint: ws://{API_HOST}/api/v1/ws/studies.
  - Handle events: study_created/updated/deleted, studies_update; extendable to database_release_*, reporting_effort_*, text_element_*.
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

