## PEARL Backend — Product Requirements Document (PRD)

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

