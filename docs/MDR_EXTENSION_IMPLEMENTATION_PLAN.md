# PEARL MDR Extension - Implementation Plan

**Version**: 1.2  
**Date**: January 2026  
**Based On**: MDR_EXTENSION_PRD.md v1.7  
**Total Estimated Hours**: 218.5  
**Total Tasks**: 163  
**Worktrees**: 11

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Implementation Overview](#2-implementation-overview)
3. [Database Strategy](#3-database-strategy)
4. [Worktree Details](#4-worktree-details)
5. [Phase Execution Order](#5-phase-execution-order)
6. [Environment Setup](#6-environment-setup)
7. [Testing Strategy](#7-testing-strategy)
8. [Merge Strategy](#8-merge-strategy)
9. [Rollback Plan](#9-rollback-plan)
10. [Dependencies & Prerequisites](#10-dependencies--prerequisites)

---

## 1. Executive Summary

### Objective

Transform PEARL into a Metadata Repository (MDR) with:
- **Standard Packages**: Cross-tenant package templates with inheritance
- **Callable Library**: Language-agnostic callable definitions with RAG search
- **Study Documents**: Upload SAP/Protocol/CRF with optional RAG search
- **Metadata Versioning**: CDISC standard version tracking with TA-IG support
- **CDISC Integration**: Import official CDISC standards via API

### Key Deliverables

| Feature | Worktrees | Hours | Key Files |
|---------|-----------|-------|-----------|
| Standard Packages | WT-1 to WT-8 | 81.5 | `packages.py`, `PackagesPage.tsx` |
| Callable Library | WT-9 | 38 | `callables.py`, `CallableLibraryPage.tsx` |
| Study Documents | WT-9 | 38 | `study_documents.py`, `StudyDocumentsPanel.tsx` |
| Metadata Versioning | WT-10 | 26 | `standard_versions.py`, `StandardVersionsPage.tsx` |
| CDISC Integration | WT-11 | 35 | `cdisc_library.py`, `CDISCImportPage.tsx` |

---

## 2. Implementation Overview

### Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                         PEARL MDR Extension                           │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────┐   ┌────────────┐ │
│  │   Standard   │   │   Callable   │   │  Study   │   │  Metadata  │ │
│  │   Packages   │   │   Library    │   │  Docs    │   │ Versioning │ │
│  │              │   │   + RAG      │   │  + RAG   │   │  + CDISC   │ │
│  └──────┬───────┘   └──────┬───────┘   └────┬─────┘   └─────┬──────┘ │
│         │                  │                │               │        │
│         │                  └────────┬───────┘               │        │
│         │                           │                       │        │
│         │                    Shared RAG/pgvector            │        │
│         │                           │                       │        │
│         ▼                           ▼                       ▼        │
│  ┌───────────────────────────────────────────────────────────────────┤
│  │                    Backend Layer (FastAPI)                        │ │
│  │  - packages.py (extended)                                         │ │
│  │  - callables.py (new)                                             │ │
│  │  - study_documents.py (new)                                       │ │
│  │  - standard_versions.py (new)                                     │ │
│  │  - cdisc_library.py (new)                                    │ │
│  └──────────────────────────────────────────────────────────────┤
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────────┤
│  │                    Database Layer                            │ │
│  │  - packages (extended with package_type, base_package_id)    │ │
│  │  - callables, callable_implementations, callable_parameters  │ │
│  │  - standard_versions, therapeutic_areas                      │ │
│  │  - cdisc_domains, cdisc_variables, cdisc_import_logs         │ │
│  │  - pgvector for semantic search                              │ │
│  └──────────────────────────────────────────────────────────────┤
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Worktree Dependency Graph

```
                         WT-1: migrations
                               │
                               ▼
                         WT-2: backend-models
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
 WT-9: callables        WT-3: backend-crud      WT-10: versioning
 (pearl_callable_db)    (pearl_core_db)         (pearl_version_db)
       │                       │                       │
       │                       ▼                       ▼
       │                WT-4: backend-api       WT-11: CDISC import
       │                       │               (pearl_version_db)
       │          ┌────────────┴───────────────────────┘
       │          │
       │          ▼
       │   WT-5: frontend-api
       │          │
       │          ▼
       │   WT-6: frontend-components
       │          │
       │          ▼
       │   WT-7: frontend-pages
       │          │
       └──────────┴────────────┐
                               ▼
                         WT-8: testing
```

---

## 3. Database Strategy

### Hybrid Database Approach

Independent worktrees use separate databases to avoid conflicts during development.

| Database | Worktrees | Purpose |
|----------|-----------|---------|
| `pearl_core_db` | WT-1, WT-2, WT-3, WT-4 | Core standard packages |
| `pearl_callable_db` | WT-9 | Callable library + Study documents (shared RAG) |
| `pearl_version_db` | WT-10, WT-11 | Versioning + CDISC (shared) |
| `pearl_main_db` | main branch | Production-like, final testing |

### Database Creation Commands

```bash
# PostgreSQL database creation
psql -U postgres -c "CREATE DATABASE pearl_core_db;"
psql -U postgres -c "CREATE DATABASE pearl_callable_db;"
psql -U postgres -c "CREATE DATABASE pearl_version_db;"
psql -U postgres -c "CREATE DATABASE pearl_main_db;"

# Enable pgvector extension (for all databases that may use vector search)
psql -U postgres -d pearl_callable_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U postgres -d pearl_version_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U postgres -d pearl_main_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Environment Files per Worktree

```bash
# backend/.env.wt_core (WT-1 to WT-4)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pearl_core_db
JWT_SECRET=dev-secret
ALLOWED_ORIGINS=["http://localhost:5173"]
ENABLE_STANDARD_PACKAGES=true

# backend/.env.wt_callable (WT-9)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pearl_callable_db
JWT_SECRET=dev-secret
OPENAI_API_KEY=sk-...
ENABLE_CALLABLE_LIBRARY=true
ENABLE_STUDY_DOCUMENTS=true
STORAGE_BACKEND=local
LOCAL_UPLOAD_PATH=./uploads/documents

# backend/.env.wt_version (WT-10, WT-11)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pearl_version_db
JWT_SECRET=dev-secret
CDISC_LIBRARY_API_KEY=your-cdisc-api-key
ENABLE_METADATA_VERSIONING=true
ENABLE_CDISC_IMPORT=true
```

---

## 4. Worktree Details

### WT-1: Migrations (7.5 hours)

**Branch**: `feature/mdr-phase1-migrations`  
**Database**: `pearl_core_db`  
**Purpose**: Create all database schema changes

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| M-1 | Create PackageType enum migration | 0.5 | None |
| M-2 | Create column addition migration | 1.5 | M-1 |
| M-3 | Create constraint migration (partial unique indexes) | 1.5 | M-2 |
| M-4 | Create RLS policy migration | 1 | M-3 |
| M-5 | Create index migration | 0.5 | M-4 |
| M-6 | Modify audit_log to allow NULL tenant_id | 0.5 | M-5 |
| M-7 | Create data migration for existing packages | 0.5 | M-6 |
| M-8 | Test migrations (apply, rollback, apply) | 1 | M-7 |
| M-9 | Document migration procedure | 0.5 | M-8 |

**Key Files to Create**:
- `backend/migrations/versions/mdr_001_add_package_type_enum.py`
- `backend/migrations/versions/mdr_002_add_package_columns.py`
- `backend/migrations/versions/mdr_003_add_constraints.py`
- `backend/migrations/versions/mdr_004_update_rls_policies.py`
- `backend/migrations/versions/mdr_005_add_indexes.py`
- `backend/migrations/versions/mdr_006_audit_log_null_tenant.py`
- `backend/migrations/versions/mdr_007_migrate_existing_packages.py`

**Completion Criteria**:
- [ ] All migrations apply cleanly to fresh database
- [ ] Rollback works for all migrations
- [ ] Existing tests pass after migrations

---

### WT-2: Backend Models (5.5 hours)

**Branch**: `feature/mdr-phase1-models`  
**Database**: `pearl_core_db`  
**Purpose**: SQLAlchemy models and Pydantic schemas

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| BM-1 | Add PackageType enum to models | 0.5 | M-7 |
| BM-2 | Update Package model with new fields | 1 | BM-1 |
| BM-3 | Add relationships (base_package, study) | 1 | BM-2 |
| BM-4 | Update Package schemas (Pydantic) | 1 | BM-3 |
| BM-5 | Add computed fields to schemas | 1 | BM-4 |
| BM-6 | Run model validator | 0.5 | BM-5 |
| BM-7 | Update __init__.py exports | 0.5 | BM-6 |

**Key Files to Modify**:
- `backend/app/models/package.py` - Add PackageType enum, new fields
- `backend/app/schemas/package.py` - Update Pydantic schemas
- `backend/app/models/__init__.py` - Export new types

**Model Changes**:
```python
# backend/app/models/package.py
class PackageType(str, Enum):
    STANDARD = "standard"
    TENANT = "tenant"
    STUDY = "study"

class Package(Base):
    # Existing fields...
    
    # New fields
    package_type: Mapped[PackageType] = mapped_column(
        SQLEnum(PackageType), default=PackageType.TENANT
    )
    base_package_id: Mapped[int | None] = mapped_column(
        ForeignKey("packages.id"), nullable=True
    )
    study_id: Mapped[int | None] = mapped_column(
        ForeignKey("studies.id"), nullable=True
    )
    created_by_super_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("super_admins.id"), nullable=True
    )
    tenant_id: Mapped[int | None]  # Changed from NOT NULL
```

**Completion Criteria**:
- [ ] Model validator passes
- [ ] All schemas export correctly
- [ ] Existing tests pass

---

### WT-3: Backend CRUD (13.5 hours)

**Branch**: `feature/mdr-phase1-crud`  
**Database**: `pearl_core_db`  
**Purpose**: Business logic for package operations

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| BC-1 | Update PackageCRUD with type filtering | 1 | BM-7 |
| BC-2 | Add STUDY package access validation | 1 | BC-1 |
| BC-3 | Add get_standards() method | 1 | BC-2 |
| BC-4 | Add create_from_standard() with deep copy | 3 | BC-3 |
| BC-5 | Add TextElement resolution for deep copy | 1.5 | BC-4 |
| BC-6 | Add inheritance chain validation | 1 | BC-5 |
| BC-7 | Add get_derived_packages() method | 1 | BC-6 |
| BC-8 | Update delete with dependency check | 1 | BC-7 |
| BC-9 | Add audit logging (NULL tenant support) | 1 | BC-8 |
| BC-10 | Write CRUD unit tests | 2 | BC-9 |

**Key Files to Modify**:
- `backend/app/crud/package.py` - Extend with new methods
- `backend/app/crud/audit_log.py` - Support NULL tenant_id

**Deep Copy Algorithm** (BC-4):
```python
async def create_from_standard(
    self, db: AsyncSession, 
    source_package_id: int,
    new_package_name: str,
    target_type: PackageType,
    tenant_id: int,
    study_id: int | None = None,
    user_id: int | None = None
) -> Package:
    # 1. Validate source is STANDARD
    # 2. Create new package with base_package_id = source
    # 3. For each PackageItem in source:
    #    a. Create new PackageItem
    #    b. Resolve TextElements (copy or reference by ID)
    # 4. Log audit trail
    # 5. Return new package
```

**Completion Criteria**:
- [ ] All CRUD methods work correctly
- [ ] Deep copy creates complete package with items
- [ ] Deletion protection works
- [ ] Audit logging captures all operations

---

### WT-4: Backend API (16.5 hours)

**Branch**: `feature/mdr-phase1-api`  
**Database**: `pearl_core_db`  
**Purpose**: REST endpoints and WebSocket broadcasts

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| BA-0 | Add feature flags to config.py | 0.5 | BC-10 |
| BA-1 | Add GET /packages/standards endpoint | 1 | BA-0 |
| BA-2 | Add POST /packages/create-from-standard | 2 | BA-1 |
| BA-3 | Add GET /packages/{id}/derived | 1 | BA-2 |
| BA-4 | Update GET /packages/ with type filter | 1 | BA-3 |
| BA-5 | Update POST /packages/ with type support | 1 | BA-4 |
| BA-6 | Update DELETE with dependency checks | 1 | BA-5 |
| BA-7 | Add super admin package CRUD endpoints | 2 | BA-6 |
| BA-8 | Add super admin PackageItem endpoints | 2 | BA-7 |
| BA-9 | Implement broadcast_to_all_tenants() | 1 | BA-8 |
| BA-10 | Add cross-tenant WebSocket broadcasts | 1 | BA-9 |
| BA-11 | Write API test script (curl) | 2 | BA-10 |
| BA-12 | Update API documentation | 1 | BA-11 |

**Key Files to Create/Modify**:
- `backend/app/core/config.py` - Add feature flags
- `backend/app/api/v1/packages.py` - Extend with new endpoints
- `backend/app/api/v1/super_admin_packages.py` - New file for super admin
- `backend/app/core/websocket.py` - Add broadcast_to_all_tenants()
- `backend/tests/scripts/test_standard_packages.sh` - New test script

**New Endpoints**:
```
GET  /api/v1/packages/standards           # List standard packages
POST /api/v1/packages/create-from-standard # Copy from standard
GET  /api/v1/packages/{id}/derived        # List derived packages

# Super Admin
POST   /api/v1/super-admin/packages/      # Create STANDARD
PUT    /api/v1/super-admin/packages/{id}  # Update STANDARD
DELETE /api/v1/super-admin/packages/{id}  # Delete STANDARD
```

**Completion Criteria**:
- [ ] All endpoints respond correctly
- [ ] Feature flags work (404 when disabled)
- [ ] WebSocket broadcasts to all tenants
- [ ] Curl test script passes

---

### WT-5: Frontend API Client (4.5 hours)

**Branch**: `feature/mdr-phase1-fe-api`  
**Database**: Uses main (backend merged)  
**Purpose**: TypeScript types and API functions

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| FA-1 | Add PackageType to TypeScript types | 0.5 | BA-10 |
| FA-2 | Update Package type with new fields | 0.5 | FA-1 |
| FA-3 | Add getStandardPackages() API function | 0.5 | FA-2 |
| FA-4 | Add createFromStandard() API function | 0.5 | FA-3 |
| FA-5 | Add getDerivedPackages() API function | 0.5 | FA-4 |
| FA-6 | Update existing package API functions | 1 | FA-5 |
| FA-7 | Add query hooks for new endpoints | 1 | FA-6 |

**Key Files to Modify**:
- `react-frontend/src/types/index.ts` - Add PackageType
- `react-frontend/src/api/endpoints/packages.ts` - Add new functions
- `react-frontend/src/api/index.ts` - Export new functions

**TypeScript Types**:
```typescript
// src/types/index.ts
export type PackageType = 'standard' | 'tenant' | 'study';

export interface Package {
  id: number;
  package_name: string;
  package_type: PackageType;
  base_package_id: number | null;
  study_id: number | null;
  tenant_id: number | null;
  // ...existing fields
}

export interface CreateFromStandardRequest {
  source_package_id: number;
  package_name: string;
  package_type: PackageType;
  study_id?: number;
}
```

**Completion Criteria**:
- [ ] All types match backend schemas
- [ ] API functions work with backend
- [ ] Query hooks properly cache/invalidate

---

### WT-6: Frontend Components (11 hours)

**Branch**: `feature/mdr-phase1-fe-components`  
**Database**: Uses main  
**Purpose**: Reusable UI components

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| FC-1 | Create PackageTypeBadge component | 1 | FA-7 |
| FC-2 | Create PackageTypeSelector component | 1 | FC-1 |
| FC-3 | Create InheritanceIndicator component | 1 | FC-2 |
| FC-4 | Create CreateFromStandardDialog | 2 | FC-3 |
| FC-5 | Create StandardPackagesList component | 2 | FC-4 |
| FC-6 | Update PackageCard with new UI | 1 | FC-5 |
| FC-7 | Create packageFilterStore (Zustand) | 1 | FC-6 |
| FC-8 | Write component tests | 2 | FC-7 |

**Key Files to Create**:
- `react-frontend/src/components/packages/PackageTypeBadge.tsx`
- `react-frontend/src/components/packages/PackageTypeSelector.tsx`
- `react-frontend/src/components/packages/InheritanceIndicator.tsx`
- `react-frontend/src/components/packages/CreateFromStandardDialog.tsx`
- `react-frontend/src/components/packages/StandardPackagesList.tsx`
- `react-frontend/src/stores/packageFilterStore.ts`

**Completion Criteria**:
- [ ] Components render correctly
- [ ] Accessibility standards met
- [ ] Component tests pass

---

### WT-7: Frontend Pages (9 hours)

**Branch**: `feature/mdr-phase1-fe-pages`  
**Database**: Uses main  
**Purpose**: Page-level integration

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| FP-1 | Update Packages page with tabs/filters | 2 | FC-8 |
| FP-2 | Update Package detail page | 2 | FP-1 |
| FP-3 | Create Super Admin Package Management page | 3 | FP-2 |
| FP-4 | Add routes for new pages | 0.5 | FP-3 |
| FP-5 | Update navigation/sidebar | 0.5 | FP-4 |
| FP-6 | Responsive design testing | 1 | FP-5 |

**Key Files to Modify/Create**:
- `react-frontend/src/features/packages/PackagesPage.tsx` - Add tabs
- `react-frontend/src/features/packages/PackageDetailPage.tsx` - Show inheritance
- `react-frontend/src/features/super-admin/StandardPackagesPage.tsx` - New
- `react-frontend/src/App.tsx` - Add routes

**Completion Criteria**:
- [ ] All pages render correctly
- [ ] Navigation works
- [ ] Responsive on mobile/tablet

---

### WT-8: Testing & Documentation (14 hours)

**Branch**: `feature/mdr-phase1-testing`  
**Database**: `pearl_main_db`  
**Purpose**: E2E tests and final documentation

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| T-1 | Write E2E test: View Standards | 1 | FP-6 |
| T-2 | Write E2E test: Create from Standard | 2 | T-1 |
| T-3 | Write E2E test: Super Admin Management | 2 | T-2 |
| T-4 | Write E2E test: RLS/Permissions | 2 | T-3 |
| T-5 | Write E2E test: Cross-tenant WebSocket | 1.5 | T-4 |
| T-6 | Run regression: test_packages_crud.sh | 0.5 | T-5 |
| T-7 | Run regression: test_preflight_comprehensive.sh | 1 | T-6 |
| T-8 | Performance testing | 1 | T-7 |
| T-9 | Update CLAUDE.md with new patterns | 1 | T-8 |
| T-10 | Document test results | 1 | T-9 |

**E2E Tests Using Browser MCP**:
```
Test 1: View Standard Packages
  - Navigate to /packages
  - Click "Standard Packages" tab
  - Verify standards list displayed
  - Verify STANDARD badge visible

Test 2: Create Package from Standard
  - Navigate to /packages
  - Click "Create from Standard"
  - Fill form and submit
  - Verify new package created with inheritance

Test 3: Super Admin Management
  - Login as super admin
  - Create standard package
  - Add items to package
  - Verify visible to all tenants
```

**Completion Criteria**:
- [ ] All E2E tests pass
- [ ] Regression tests pass
- [ ] Performance < 500ms for package list
- [ ] CLAUDE.md updated

---

### WT-9: Callable Library + Study Documents (76 hours)

**Branch**: `feature/mdr-phase1-callables`  
**Database**: `pearl_callable_db`  
**Purpose**: Language-agnostic callable definitions with RAG + Study document management

#### Part A: Callable Library (38 hours)

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| CL-1 | Install pgvector, create migration | 1 | M-9 |
| CL-2 | Create Callable, CallableImplementation models | 2.5 | CL-1, BM-7 |
| CL-3 | Create ParameterLanguageMapping model | 1 | CL-2 |
| CL-4 | Create CallableDocumentation model (vector) | 1 | CL-3 |
| CL-5 | Create Callable schemas | 1.5 | CL-4 |
| CL-6 | Create CallableCRUD | 2 | CL-5 |
| CL-7 | Create CallableImplementationCRUD | 1.5 | CL-6 |
| CL-8 | Create embedding service (OpenAI) | 2 | CL-7 |
| CL-9 | Create vector search function | 1.5 | CL-8 |
| CL-10 | Create RAG service | 3 | CL-9 |
| CL-11 | Create callable API endpoints | 2 | CL-10 |
| CL-12 | Create implementation endpoints | 1 | CL-11 |
| CL-13 | Create search endpoint | 1 | CL-12 |
| CL-14 | Create /callables/ask RAG endpoint | 2 | CL-13 |
| CL-15 | Create super admin endpoints | 1 | CL-14 |
| CL-16 | Create TypeScript types | 0.5 | CL-15 |
| CL-17 | Create API client functions | 1 | CL-16 |
| CL-18 | Create CallableLibraryPage | 2 | CL-17 |
| CL-19 | Create CallableSearchBar | 1.5 | CL-18 |
| CL-20 | Create CallableAskDialog (RAG UI) | 2 | CL-19 |
| CL-21 | Create CallableDetailView | 2 | CL-20 |
| CL-22 | Create LanguageImplementationEditor | 1.5 | CL-21 |
| CL-23 | Create CallableDocEditor | 1.5 | CL-22 |
| CL-24 | Write E2E tests | 2 | CL-23 |
| CL-25 | Write curl test script | 1 | CL-24 |

#### Part B: Study Document Management (38 hours)

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| SD-1 | Create StudyDocument model | 1.5 | CL-1, BM-7 |
| SD-2 | Create StudyDocumentChunk model (vector) | 1 | SD-1 |
| SD-3 | Create StudyDocument schemas | 1 | SD-2 |
| SD-4 | Create document parser service (PDF, Word, Excel, TXT, Markdown) | 3 | SD-3 |
| SD-5 | Create document chunking service | 2 | SD-4 |
| SD-6 | Create document vectorization service (reuses CL-8) | 1.5 | SD-5, CL-8 |
| SD-7 | Create StudyDocumentCRUD (CRUD + file storage) | 2 | SD-6 |
| SD-8 | Create document search function (reuses CL-9) | 1 | SD-7, CL-9 |
| SD-9 | Create document RAG service (reuses CL-10) | 2 | SD-8, CL-10 |
| SD-10 | Create document CRUD endpoints | 2 | SD-9 |
| SD-11 | Create vectorization endpoints | 1.5 | SD-10 |
| SD-12 | Create study document search endpoint | 1 | SD-11 |
| SD-13 | Create /studies/{id}/documents/ask RAG endpoint | 1.5 | SD-12 |
| SD-14 | Create cross-study search endpoints | 1 | SD-13 |
| SD-15 | Create unified /unified/ask endpoint | 2 | SD-14, CL-14 |
| SD-16 | Create StudyDocument TypeScript types | 0.5 | SD-15 |
| SD-17 | Create document API client functions | 1 | SD-16 |
| SD-18 | Create StudyDocumentsPanel component | 2 | SD-17 |
| SD-19 | Create DocumentUploadDialog | 2 | SD-18 |
| SD-20 | Create DocumentViewer | 1.5 | SD-19 |
| SD-21 | Create DocumentAskDialog | 2 | SD-20 |
| SD-22 | Create UnifiedSearchDialog | 2 | SD-21 |
| SD-23 | Add Documents tab to Study page | 1 | SD-22 |
| SD-24 | Write study documents E2E tests | 2 | SD-23 |
| SD-25 | Write curl test script | 1 | SD-24 |

**Migrations Created by WT-9** (in pearl_callable_db):
```
callable_001_create_pgvector.py        # Enable vector extension
callable_002_create_callable_tables.py # callables, implementations, parameters, documentation
callable_003_create_study_document_tables.py  # study_documents, study_document_chunks
```

**Key Files to Create**:

*Callable Library:*
- `backend/app/models/callable.py`
- `backend/app/models/callable_implementation.py`
- `backend/app/models/callable_documentation.py`
- `backend/app/crud/callable.py`
- `backend/app/services/embedding_service.py`
- `backend/app/services/rag_service.py`
- `backend/app/services/storage_service.py` (LocalStorage + S3Storage)
- `backend/app/api/v1/callables.py`
- `react-frontend/src/features/callables/CallableLibraryPage.tsx`

*Study Documents:*
- `backend/app/models/study_document.py`
- `backend/app/models/study_document_chunk.py`
- `backend/app/crud/study_document.py`
- `backend/app/services/document_parser.py`
- `backend/app/services/document_chunker.py`
- `backend/app/api/v1/study_documents.py`
- `react-frontend/src/features/study-documents/StudyDocumentsPanel.tsx`
- `react-frontend/src/features/study-documents/DocumentUploadDialog.tsx`
- `react-frontend/src/features/study-documents/UnifiedSearchDialog.tsx`

**Python Dependencies** (add to requirements.txt):
```
PyMuPDF>=1.23.0       # PDF parsing
python-docx>=1.0.0    # Word document parsing
openpyxl>=3.1.0       # Excel parsing
pgvector>=0.2.0       # Vector storage
openai>=1.0.0         # Embeddings and RAG
boto3>=1.28.0         # S3 storage (optional)
```

**E2E Test Cases for Callables (CL-24)**:
```
1. Create callable with SAS implementation
2. Add R implementation to existing callable
3. Search callables by keyword
4. Semantic search for callables
5. Ask RAG question and verify response
6. Super admin create global callable
7. Verify tenant isolation (can't see other tenant callables)
```

**E2E Test Cases for Study Documents (SD-24)**:
```
1. Upload PDF document to study
2. Upload Word document to study
3. View document list
4. Download document
5. Toggle vectorization on
6. Wait for vectorization complete
7. Search within study documents
8. Ask RAG question about study documents
9. Cross-study search (verify user can only see accessible studies)
10. Unified search (callables + documents)
11. Delete document (verify cascade deletes chunks)
12. Test file size limit validation
13. Test file type validation
```

**Curl Test Scripts**:
- `backend/tests/scripts/test_callable_library.sh`
- `backend/tests/scripts/test_callable_rag.sh`
- `backend/tests/scripts/test_study_documents.sh`
- `backend/tests/scripts/test_document_rag.sh`
- `backend/tests/scripts/test_unified_search.sh`

**Completion Criteria**:
- [ ] Callables can be created with multiple language implementations
- [ ] Semantic search returns relevant results for callables
- [ ] RAG endpoint provides helpful responses for callables
- [ ] Documents can be uploaded (PDF, Word, Excel, TXT, Markdown)
- [ ] Documents can be vectorized (user chooses)
- [ ] Document validation (size, type) works correctly
- [ ] Study document RAG search works within single study
- [ ] Cross-study document search works (only accessible studies)
- [ ] Unified search (callables + documents) works
- [ ] Audit logging captures all document operations
- [ ] WebSocket broadcasts document changes

---

### WT-10: Metadata Versioning (26 hours)

**Branch**: `feature/mdr-phase1-versioning`  
**Database**: `pearl_version_db`  
**Purpose**: Standard version tracking with TA-IG support

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| MV-1 | Create StandardType enum | 0.5 | M-9 |
| MV-2 | Create StandardVersion model | 2 | MV-1, BM-7 |
| MV-3 | Create TherapeuticArea table | 1 | MV-2 |
| MV-4 | Create callable_standard_versions junction | 1 | MV-3 |
| MV-5 | Add target_standard_version_id to packages | 0.5 | MV-4 |
| MV-6 | Create StandardVersion schemas | 1 | MV-5 |
| MV-7 | Create StandardVersionCRUD | 2 | MV-6 |
| MV-8 | Create TherapeuticAreaCRUD | 1.5 | MV-7 |
| MV-9 | Create tenant API endpoints | 2 | MV-8 |
| MV-10 | Create super admin endpoints | 1.5 | MV-9 |
| MV-11 | Update package API for version_id | 1 | MV-10 |
| MV-12 | Update callable API for version links | 1 | MV-11 |
| MV-13 | Create TypeScript types | 0.5 | MV-12 |
| MV-14 | Create API client functions | 1 | MV-13 |
| MV-15 | Create StandardVersionsPage | 2 | MV-14 |
| MV-16 | Create StandardVersionSelector | 1 | MV-15 |
| MV-17 | Create StandardVersionBadge | 0.5 | MV-16 |
| MV-18 | Create StandardVersionTree (lineage) | 2 | MV-17 |
| MV-19 | Update Package forms | 1 | MV-18 |
| MV-20 | Write E2E tests | 2 | MV-19 |
| MV-21 | Write curl test script | 1 | MV-20 |

**Key Files to Create**:
- `backend/app/models/standard_version.py`
- `backend/app/models/therapeutic_area.py`
- `backend/app/crud/standard_version.py`
- `backend/app/api/v1/standard_versions.py`
- `react-frontend/src/features/versioning/StandardVersionsPage.tsx`

**Completion Criteria**:
- [ ] Standard versions can be created with parent relationships
- [ ] TA-IGs inherit from base standards
- [ ] Version lineage visualization works
- [ ] Packages can target specific versions

---

### WT-11: CDISC Library Integration (35 hours)

**Branch**: `feature/mdr-phase1-cdisc`  
**Database**: `pearl_version_db` (shared with WT-10)  
**Purpose**: Import official CDISC standards

| Task ID | Task | Hours | Dependencies |
|---------|------|-------|--------------|
| CI-1 | Add CDISC config to settings | 0.5 | MV-21 |
| CI-2 | Create CDISCDomain, CDISCVariable models | 2 | CI-1 |
| CI-3 | Create CDISCImportLog model | 1 | CI-2 |
| CI-4 | Add CDISC tracking to StandardVersion | 1 | CI-3 |
| CI-5 | Create CDISC schemas | 1.5 | CI-4 |
| CI-6 | Create CDISCLibraryClient service | 3 | CI-5 |
| CI-7 | Create import service (mapping) | 4 | CI-6 |
| CI-8 | Create CDISCDomain CRUD | 1.5 | CI-7 |
| CI-9 | Create CDISCVariable CRUD | 1.5 | CI-8 |
| CI-10 | Create browse products endpoint | 1 | CI-9 |
| CI-11 | Create import preview endpoint | 1.5 | CI-10 |
| CI-12 | Create import standard endpoint | 2 | CI-11 |
| CI-13 | Create import history endpoint | 1 | CI-12 |
| CI-14 | Create domain/variable read endpoints | 1 | CI-13 |
| CI-15 | Create TypeScript types | 0.5 | CI-14 |
| CI-16 | Create API client functions | 1 | CI-15 |
| CI-17 | Create CDISCImportPage | 2.5 | CI-16 |
| CI-18 | Create CDISCProductBrowser | 2 | CI-17 |
| CI-19 | Create CDISCImportPreview dialog | 2 | CI-18 |
| CI-20 | Create CDISCDomainViewer | 2 | CI-19 |
| CI-21 | Write E2E tests | 2 | CI-20 |
| CI-22 | Write curl test script | 1 | CI-21 |

**Key Files to Create**:
- `backend/app/models/cdisc_domain.py`
- `backend/app/models/cdisc_variable.py`
- `backend/app/models/cdisc_import_log.py`
- `backend/app/services/cdisc_library_client.py`
- `backend/app/services/cdisc_import_service.py`
- `backend/app/api/v1/cdisc_library.py`
- `react-frontend/src/features/cdisc/CDISCImportPage.tsx`

**Completion Criteria**:
- [ ] CDISC products can be browsed
- [ ] Standards can be previewed before import
- [ ] Import creates StandardVersion + domains + variables
- [ ] Import history tracked with status

---

## 5. Phase Execution Order

### Recommended Sequence

```
Week 1-2: Foundation
├── WT-1: Migrations (7.5 hrs) - Day 1-2
├── WT-2: Models (5.5 hrs) - Day 2-3
└── MERGE to main - Day 3

Week 2-3: Core Backend (parallel tracks start)
├── WT-3: CRUD (13.5 hrs) - Day 4-6
├── WT-4: API (16.5 hrs) - Day 6-9
├── [parallel] WT-9: Callables (38 hrs) - Day 4-14
└── [parallel] WT-10: Versioning (26 hrs) - Day 4-12

Week 3-4: Frontend + CDISC
├── WT-5: FE API (4.5 hrs) - Day 10
├── WT-6: FE Components (11 hrs) - Day 10-12
├── WT-7: FE Pages (9 hrs) - Day 12-14
└── [parallel] WT-11: CDISC (35 hrs) - Day 12-18

Week 4-5: Integration
├── Merge all worktrees to main
├── WT-8: Testing (14 hrs) - Day 19-21
└── Final documentation and cleanup
```

### Critical Milestones

| Milestone | Target | Dependencies |
|-----------|--------|--------------|
| Schema Complete | Day 3 | WT-1, WT-2 merged |
| Backend API Ready | Day 9 | WT-3, WT-4 merged |
| Callable Library Ready | Day 14 | WT-9 merged |
| Versioning Ready | Day 12 | WT-10 merged |
| Frontend Ready | Day 14 | WT-5, WT-6, WT-7 merged |
| CDISC Import Ready | Day 18 | WT-11 merged |
| Testing Complete | Day 21 | WT-8 complete |

---

## 6. Environment Setup

### Prerequisites

```bash
# Backend
Python 3.11+
PostgreSQL 15+ with pgvector extension
uv package manager

# Frontend
Node.js 18+
npm 9+

# External Services
OpenAI API key (for RAG)
CDISC Library API key (for imports)
```

### Worktree Setup Commands

```bash
# From main PEARL repository
cd c:\python\PEARL

# Create databases
psql -U postgres -c "CREATE DATABASE pearl_core_db;"
psql -U postgres -c "CREATE DATABASE pearl_callable_db;"
psql -U postgres -c "CREATE DATABASE pearl_version_db;"
psql -U postgres -c "CREATE DATABASE pearl_main_db;"

# Enable pgvector
psql -U postgres -d pearl_callable_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U postgres -d pearl_main_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create worktrees
git worktree add ../pearl-wt-migrations feature/mdr-phase1-migrations
git worktree add ../pearl-wt-models feature/mdr-phase1-models
git worktree add ../pearl-wt-crud feature/mdr-phase1-crud
git worktree add ../pearl-wt-api feature/mdr-phase1-api
git worktree add ../pearl-wt-callables feature/mdr-phase1-callables
git worktree add ../pearl-wt-versioning feature/mdr-phase1-versioning
git worktree add ../pearl-wt-cdisc feature/mdr-phase1-cdisc
git worktree add ../pearl-wt-fe-api feature/mdr-phase1-fe-api
git worktree add ../pearl-wt-fe-components feature/mdr-phase1-fe-components
git worktree add ../pearl-wt-fe-pages feature/mdr-phase1-fe-pages
git worktree add ../pearl-wt-testing feature/mdr-phase1-testing

# Setup environment for each worktree
# (copy appropriate .env file to each worktree's backend folder)
```

---

## 7. Testing Strategy

### Test Layers

| Layer | Tool | Coverage |
|-------|------|----------|
| Unit Tests | pytest | CRUD functions, services |
| API Tests | curl scripts | All endpoints |
| Component Tests | Vitest | React components |
| E2E Tests | Browser MCP | Full user flows |
| Integration | Browser MCP + API | Frontend + Backend |

### Regression Tests (Must Pass)

```bash
# Run from backend/
./tests/scripts/test_packages_crud.sh
./tests/scripts/test_crud_simple.sh
./tests/scripts/test_preflight_comprehensive.sh
./tests/scripts/test_role_based_permissions.sh
./tests/scripts/test_audit_logging.sh
```

### New Test Scripts

```bash
# Standard Packages
./tests/scripts/test_standard_packages.sh
./tests/scripts/test_package_inheritance.sh
./tests/scripts/test_package_rls.sh
./tests/scripts/test_super_admin_packages.sh

# Callable Library
./tests/scripts/test_callable_library.sh
./tests/scripts/test_callable_rag.sh

# Study Documents
./tests/scripts/test_study_documents.sh
./tests/scripts/test_document_rag.sh
./tests/scripts/test_unified_search.sh
./tests/scripts/test_document_validation.sh

# Versioning
./tests/scripts/test_standard_versions.sh
./tests/scripts/test_therapeutic_areas.sh

# CDISC
./tests/scripts/test_cdisc_import.sh
```

---

## 8. Merge Strategy

### Pre-Merge Checklist

Before merging any worktree to main:

- [ ] Pull latest main into worktree
- [ ] Rebase migrations if main has new ones
- [ ] Run `uv run alembic upgrade head` on fresh DB
- [ ] Run `uv run python tests/validator/run_model_validation.py`
- [ ] Run all regression tests
- [ ] Resolve any merge conflicts
- [ ] Code review completed

### Handling Multiple Heads

When merging worktrees with parallel migrations:

```bash
# Check for multiple heads
alembic heads

# If multiple heads exist (e.g., abc123, def456)
alembic merge -m "merge feature branches" abc123 def456

# Apply merged migration
alembic upgrade head
```

### Merge Order

1. **WT-1** (migrations) - First, establishes schema
2. **WT-2** (models) - After WT-1
3. **WT-3** (crud) - After WT-2
4. **WT-4** (api) - After WT-3
5. **WT-10** (versioning) - Can merge before or with WT-4
6. **WT-9** (callables) - Can merge with WT-4/WT-10
7. **WT-11** (cdisc) - After WT-10
8. **WT-5** (fe-api) - After backend merged
9. **WT-6** (fe-components) - After WT-5
10. **WT-7** (fe-pages) - After WT-6
11. **WT-8** (testing) - Last

---

## 9. Rollback Plan

### Migration Rollback

```bash
# Rollback all Phase 1 migrations
alembic downgrade mdr_001-1

# Rollback to specific migration
alembic downgrade mdr_003
```

### Feature Flag Disable

If issues found in production:

```python
# backend/.env
ENABLE_STANDARD_PACKAGES=false
ENABLE_CALLABLE_LIBRARY=false
ENABLE_METADATA_VERSIONING=false
ENABLE_CDISC_IMPORT=false
```

This hides all new UI and returns 404 for new endpoints, without database rollback.

### Full Rollback

If critical issues require full rollback:

1. Disable all feature flags
2. Roll back migrations: `alembic downgrade mdr_001-1`
3. Revert Git commits on main
4. Deploy previous stable version

---

## 10. Dependencies & Prerequisites

### External Services

| Service | Purpose | Required For |
|---------|---------|--------------|
| PostgreSQL 15+ | Database | All |
| pgvector | Vector search | WT-9 |
| OpenAI API | Embeddings + RAG | WT-9 |
| CDISC Library API | Standards import | WT-11 |

### Environment Variables

```bash
# Required for all
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=...
ALLOWED_ORIGINS=["http://localhost:5173"]

# Feature Flags
ENABLE_STANDARD_PACKAGES=false
ENABLE_CALLABLE_LIBRARY=false
ENABLE_METADATA_VERSIONING=false
ENABLE_CDISC_IMPORT=false

# Callable Library (WT-9)
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-ada-002
RAG_LLM_MODEL=gpt-4-turbo
OPENAI_RATE_LIMIT_PER_MINUTE=60
ENABLE_RAG_FALLBACK=true

# CDISC Import (WT-11)
CDISC_LIBRARY_API_KEY=...
CDISC_LIBRARY_BASE_URL=https://library.cdisc.org/api
```

### Python Dependencies (Add to requirements.txt)

```
# WT-9: Callable Library + Study Documents
pgvector>=0.2.0       # Vector storage
openai>=1.0.0         # Embeddings and RAG
PyMuPDF>=1.23.0       # PDF parsing
python-docx>=1.0.0    # Word document parsing
openpyxl>=3.1.0       # Excel parsing

# WT-11: CDISC Import
httpx>=0.25.0         # For async CDISC API calls
```

### npm Dependencies (Add to package.json)

```json
{
  "dependencies": {
    "@uiw/react-md-editor": "^4.0.0"  // For callable documentation editor
  }
}
```

---

## Summary

| Metric | Value |
|--------|-------|
| Total Worktrees | 11 |
| Total Tasks | 163 |
| Total Hours | 218.5 |
| Parallel Tracks | 3 (Core, Callable+Docs, Versioning/CDISC) |
| Estimated Wall Time | 60-70 hours with parallelization |

### Quick Reference

```
Core Path:    WT-1 → WT-2 → WT-3 → WT-4 → WT-5 → WT-6 → WT-7 → WT-8
Callable+Docs: WT-9 (parallel after WT-2) - includes Study Documents
Versioning:   WT-10 → WT-11 (parallel after WT-2)
```

### Feature Summary

| Feature | Tasks | Hours |
|---------|-------|-------|
| Standard Packages (Core) | 70 | 81.5 |
| Callable Library | 25 | 38 |
| Study Documents | 25 | 38 |
| Metadata Versioning | 21 | 26 |
| CDISC Import | 22 | 35 |
| **Total** | **163** | **218.5** |

---

*Document Version: 1.2*  
*Last Updated: January 2026*  
*Based on: MDR_EXTENSION_PRD.md v1.7*
