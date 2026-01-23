# PEARL MDR Extension - Product Requirements Document

**Version**: 1.7  
**Date**: January 2026  
**Status**: Draft (Implementation Plan Feedback Addressed)  
**Scope**: Phase 1 MVP - Standard Packages + Callable Library + Study Documents + Metadata Versioning + CDISC Import

**Revision History**:
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial draft |
| 1.1 | Jan 2026 | Addressed critical gaps from PRD feedback review |
| 1.2 | Jan 2026 | Added Macro Library with RAG, language-agnostic design |
| 1.3 | Jan 2026 | Added Metadata Versioning, renamed Macro to Callable, multi-language support |
| 1.4 | Jan 2026 | Added CDISC Library integration, TA Implementation Guides |
| 1.5 | Jan 2026 | Addressed v2 feedback: extensibility, idempotency, deletion protection |
| 1.6 | Jan 2026 | Added Study Document Management with RAG |
| 1.7 | Jan 2026 | Addressed implementation plan feedback |

**v1.7 Changes** (Implementation Plan Feedback):
- Added `ENABLE_STUDY_DOCUMENTS` feature flag (Section 6.7)
- Added file storage strategy: local + S3 support (Section 5.9.1)
- Added document validation rules: size/type limits (Section 5.9.1)
- Added audit logging for document operations (Section 5.9.1)
- Added unified search scope/access control specification (Section 6.10)
- Clarified RLS policies for study documents (Section 5.9.1)

**v1.6 Changes** (Study Document Management):
- Added Study Document Management feature (Section 3 item 9)
- Added StudyDocument, StudyDocumentChunk models (Section 5.9.1)
- Support for PDF, Word, Excel, TXT, Markdown file formats
- Optional per-document vectorization (user-controlled)
- Study-scoped and cross-study RAG search
- Unified search endpoint (callables + documents)
- Added 25 new tasks to WT-9 (SD-1 to SD-25, 38 hours)
- Total tasks: 163, Total hours: 218.5

**v1.5 Changes** (Feedback Gaps Addressed):
- Changed TherapeuticArea from enum to lookup table (runtime extensibility)
- Added feature flags for all features: `ENABLE_CALLABLE_LIBRARY`, `ENABLE_METADATA_VERSIONING`, `ENABLE_CDISC_IMPORT`
- Specified CDISC import idempotency rules (`on_conflict: skip|update|error`)
- Added deletion protection rules for StandardVersion, Callable, TherapeuticArea
- Documented CDISC → PEARL mapping algorithm (FR-8.4)
- Updated worktree dependency graph with WT-9, WT-10, WT-11
- Added OpenAI rate limiting and cost control configuration
- Added WebSocket events for callables, standard versions, CDISC imports
- Added vector index tuning guidelines
- Specified RAG multi-tenant search scope (global + tenant, with boost)
- Added deprecation cascade behavior documentation
- Added initial STANDARD package creation workflows (manual, CDISC, seed)
- **Added hybrid database strategy**: Grouped DBs for related worktrees (Section 8.1.1)
- **Added migration merge strategy**: Alembic merge heads workflow (Section 8.1.2)

**v1.4 Changes**:
- Added CDISC Library API integration (FR-8, Section 5.11, Section 6.9)
- Added TherapeuticArea and TA-IG support (Oncology, Cardiovascular, etc.)
- Added CDISCDomain, CDISCVariable, CDISCImportLog models
- Added CDISC import endpoints for super admin
- Added import preview and browse CDISC products functionality
- Added WT-11: CDISC Import worktree (35 hours)
- Total tasks: 138, Total hours: 180.5
- CDISC Library API tested and working

**v1.3 Changes**:
- Renamed "Macro" to "Callable" for language independence (Section 5.12)
- Added CallableImplementation table for multi-language support
- Added ParameterLanguageMapping for language-specific syntax
- Added Metadata Versioning System (FR-7, Section 5.10)
- Added StandardVersion model with variant/amendment tracking
- Added callable_standard_versions junction table
- Updated API endpoints from `/macros/` to `/callables/`
- Added WT-10: Metadata Versioning worktree (26 hours)
- Updated WT-9: Callable Library (38 hours, renamed from Macro Library)

**v1.2 Changes**:
- Added Macro Library with RAG (FR-6, Section 5.9)
- Added pgvector for semantic search
- Language-agnostic parameter types
- Multi-language examples support

**v1.1 Critical Gaps Addressed**:
- Super admin RLS bypass mechanism (Section 5.4)
- `created_by_super_admin_id` field for STANDARD packages (Section 5.1)
- STUDY package access control in CRUD layer (Section 5.5)
- PackageItem deep copy specification (Section 5.7)
- Cross-tenant WebSocket broadcasting (Section 6.5)
- Feature flag implementation (Section 6.7)
- Partial unique index syntax fix (Section 5.2)
- Audit log NULL tenant_id support (Section 5.8)
- Super admin PackageItem endpoints (Section 6.4)
- Error message specifications (Section 6.6)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Goals](#2-problem-statement--goals)
3. [Scope Definition](#3-scope-definition)
4. [Functional Requirements](#4-functional-requirements)
5. [Data Model Specification](#5-data-model-specification)
6. [API Contract Definitions](#6-api-contract-definitions)
7. [Frontend Components](#7-frontend-components)
8. [Worktree Strategy & Parallel Development](#8-worktree-strategy--parallel-development)
9. [Database Migration Strategy](#9-database-migration-strategy)
10. [Testing Strategy](#10-testing-strategy)
11. [Task Breakdown & Dependencies](#11-task-breakdown--dependencies)
12. [Risk Assessment](#12-risk-assessment)
13. [Future Phases Overview](#13-future-phases-overview)

---

## 1. Executive Summary

### Vision

Transform PEARL from a tracker application into a full-fledged Metadata Repository (MDR) with code generation capabilities, aligned with CDISC standards (ARS v1.0, SDTM/ADaM IGs).

### Phase 1 MVP Objective

Implement **Standard Packages** - a foundational feature that enables:
- Super admin to maintain global package templates accessible to all tenants
- Tenants to create study-specific packages from standards with customization
- Inheritance tracking between standard and customized packages

### Success Criteria

1. Super admin can create/manage STANDARD packages visible to all tenants
2. Tenants can copy STANDARD packages to create TENANT or STUDY packages
3. Inheritance is tracked (source package reference maintained)
4. All existing functionality continues to work (backward compatibility)
5. Automated tests pass for all new functionality

---

## 2. Problem Statement & Goals

### Current State

- Packages are tenant-scoped only (`tenant_id` NOT NULL)
- No concept of global/standard packages
- No inheritance or template system
- Each tenant creates packages from scratch
- No way to share best practices across tenants

### Desired State

- Three package types: STANDARD, TENANT, STUDY
- STANDARD packages are global (managed by super admin)
- TENANT packages are tenant-specific (current behavior)
- STUDY packages are study-specific customizations
- Clear inheritance chain with tracking

### Goals

| Goal | Metric | Target |
|------|--------|--------|
| Global package availability | STANDARD packages visible to all tenants | 100% |
| Adoption rate | Tenants using "Create from Standard" | Track usage |
| Backward compatibility | Existing tests pass | 100% |
| Performance | Package list load time | < 500ms |

---

## 3. Scope Definition

### In Scope (Phase 1 MVP)

1. **Package Type System**
   - Add `package_type` enum: STANDARD, TENANT, STUDY
   - Add `base_package_id` for inheritance tracking
   - Add `study_id` for STUDY-type packages

2. **RLS Policy Changes**
   - STANDARD packages readable by all tenants
   - TENANT packages readable only by owning tenant
   - STUDY packages readable by users with study access

3. **Super Admin Management**
   - Create/edit/delete STANDARD packages
   - View all packages across tenants (existing capability)

4. **Tenant Operations**
   - View STANDARD packages in package list
   - "Create from Standard" action
   - Customize copied package (becomes TENANT or STUDY type)

5. **Inheritance Tracking**
   - `base_package_id` points to source package
   - UI shows inheritance lineage
   - Audit log captures copy operations

6. **Macro Library with RAG** (NEW)
   - Store callable definitions (macros/functions) with parameters
   - Language-agnostic: each callable can have implementations in multiple languages
   - Store documentation (markdown) for semantic search
   - pgvector for RAG-based recommendations
   - Multi-language program support (SAS Viya style)

7. **Metadata Versioning System** (NEW)
   - Standard versions (SDTM 3.2, ADaM 1.1, ARS 1.0)
   - Variant/amendment tracking within versions (e.g., SDTM 3.2-COVID)
   - Therapeutic Area Implementation Guides (Oncology, Cardiovascular, etc.)
   - Link packages, callables, text elements to standard versions
   - Version history and changelog tracking
   - Super admin manages standard versions

8. **CDISC Library Integration** (NEW)
   - Import official CDISC standards via CDISC Library API
   - Import SDTM, ADaM, CDASH, SEND standards and Implementation Guides
   - Import domains with full variable metadata (name, label, core, datatype)
   - Manual import by super admin (on-demand)
   - 100% CDISC compliant foundation that tenants can customize

9. **Study Document Management with RAG** (NEW)
   - Upload study-level documents: SAP, Protocol, CRF, Annotated CRF
   - Support all common formats: PDF, Word (.docx), Excel (.xlsx), TXT, Markdown
   - Optional vectorization per document (user chooses)
   - Query documents within single study or across accessible studies
   - Separate study document RAG endpoint + unified search option
   - Shares pgvector/OpenAI infrastructure with Callable Library (WT-9)

### Out of Scope (Phase 1)

- Automated sync/scheduled updates from CDISC (deferred to Phase 1.1)
- Dataset specifications with macro automation (Phase 2)
- Full ARS compliance (Phase 3)
- Controlled Terminology full import (Phase 2 - basic CT in Phase 1)
- Program generation/execution (PEARL stores metadata only)

### Dependencies

- Existing Package/PackageItem models
- Existing RLS infrastructure
- Super admin authentication system
- Multi-tenant middleware

**Callable Library Additional Dependencies**:
- pgvector PostgreSQL extension
- OpenAI API key (for embeddings and RAG)
- LLM integration service (OpenAI GPT-4 or similar)

**CDISC Library Dependencies**:
- CDISC Library API key (from CDISC Library portal)
- Network access to `https://library.cdisc.org/api`

### Environment Variables (New)

```
# Callable Library / RAG Configuration
OPENAI_API_KEY=sk-...                    # Required for embeddings and RAG
EMBEDDING_MODEL=text-embedding-ada-002   # Default embedding model
RAG_LLM_MODEL=gpt-4-turbo               # LLM for RAG responses

# OpenAI Rate Limiting & Cost Control
OPENAI_RATE_LIMIT_PER_MINUTE=60          # Max API calls per minute
OPENAI_MONTHLY_BUDGET_USD=100.0          # Monthly spending limit (optional)
EMBEDDING_BATCH_SIZE=100                  # Batch size for bulk embedding generation
ENABLE_RAG_FALLBACK=true                 # Return search-only results if LLM unavailable

# CDISC Library Integration
CDISC_LIBRARY_API_KEY=your-api-key       # Required for CDISC imports
CDISC_LIBRARY_BASE_URL=https://library.cdisc.org/api  # Default, can override

# Feature Flags
ENABLE_STANDARD_PACKAGES=false
ENABLE_CALLABLE_LIBRARY=false
ENABLE_METADATA_VERSIONING=false
ENABLE_CDISC_IMPORT=false
```

**OpenAI Fallback Behavior** (when `ENABLE_RAG_FALLBACK=true`):
- If OpenAI API unavailable: `/callables/ask` returns top search results without LLM summary
- If rate limited: Queue request and return 429 with retry-after header
- If budget exceeded: Return 402 "Monthly AI budget exceeded" (admin notification sent)

---

## 4. Functional Requirements

### FR-1: Package Type System

**FR-1.1**: Package Type Enum
- System SHALL support three package types: STANDARD, TENANT, STUDY
- Default type for new packages SHALL be TENANT (backward compatible)
- Type CANNOT be changed after creation (immutable)

**FR-1.2**: Package Type Constraints
- STANDARD packages: `tenant_id` IS NULL, `study_id` IS NULL
- TENANT packages: `tenant_id` IS NOT NULL, `study_id` IS NULL
- STUDY packages: `tenant_id` IS NOT NULL, `study_id` IS NOT NULL

**FR-1.3**: Inheritance Tracking
- `base_package_id` MAY reference another package
- Inheritance chain: STANDARD → TENANT → STUDY (or STANDARD → STUDY)
- Self-reference NOT allowed
- Circular references NOT allowed

### FR-2: Access Control

**FR-2.1**: STANDARD Package Visibility
- All authenticated users CAN view STANDARD packages (read-only)
- Only super admin CAN create/edit/delete STANDARD packages

**FR-2.2**: TENANT Package Visibility
- Users CAN view/edit TENANT packages within their tenant
- Admin users CAN create/delete TENANT packages

**FR-2.3**: STUDY Package Visibility
- Users with study access CAN view STUDY packages
- Users with LEAD role CAN create/edit/delete STUDY packages

### FR-3: Super Admin Operations

**FR-3.1**: Standard Package Management
- Super admin CAN create new STANDARD packages
- Super admin CAN edit STANDARD package metadata
- Super admin CAN add/remove/edit items in STANDARD packages
- Super admin CAN delete STANDARD packages (with dependency check)

**FR-3.2**: Deletion Protection
- System SHALL prevent deletion if packages reference as `base_package_id`
- System SHALL show count of dependent packages before deletion attempt

### FR-4: Tenant Operations

**FR-4.1**: View Standard Packages
- Package list SHALL show STANDARD packages in separate section/tab
- STANDARD packages SHALL be visually distinguished (badge/icon)
- STANDARD packages SHALL be read-only for non-super-admin users

**FR-4.2**: Create from Standard
- User CAN select "Create from Standard" action on any STANDARD package
- System SHALL create copy as TENANT or STUDY type
- System SHALL copy all PackageItems and related details
- System SHALL set `base_package_id` to source STANDARD package
- User CAN customize package name and metadata during copy

**FR-4.3**: Inheritance Display
- Package detail view SHALL show inheritance lineage
- "Based on: [Standard Package Name]" indicator
- Link to view original standard package

### FR-5: Audit & Tracking

**FR-5.1**: Audit Logging
- All STANDARD package operations SHALL be logged
- Copy operations SHALL log source and destination package IDs
- Audit log SHALL include user, timestamp, action, details

**FR-5.2**: Statistics
- System SHOULD track usage statistics for STANDARD packages
- Count of packages derived from each standard
- Most frequently copied standards

### FR-6: Macro Library (Language-Agnostic)

**Design Philosophy**: The macro library is programming language independent. It stores 
metadata about callable units (macros, functions, modules) regardless of implementation 
language. This supports industry evolution from SAS to R/Python while allowing tenants 
to use any language or combination of languages.

**FR-6.1**: Macro/Function Registration
- Tenants CAN register callable units with name, language(s), and parameter definitions
- Language is a free-form string field (e.g., "SAS", "R", "Python", "SAS/R", "Any")
- Each parameter SHALL have: name, label, type, required flag, default value
- Parameter types are language-agnostic: data, variable, variables, expression, literal, code_block
- A single callable CAN have examples in multiple languages
- Super admin CAN create global macros (visible to all tenants)

**FR-6.2**: Multi-Language Documentation
- Each macro CAN have markdown documentation attached
- Documentation SHALL include: summary, description, parameters, examples
- Examples CAN be tagged by language (SAS, R, Python, etc.)
- Documentation SHALL support versioning
- System SHALL store usage examples as structured data with language tags

**FR-6.3**: Semantic Search (pgvector)
- System SHALL generate embeddings for macro documentation
- Users CAN search macros by natural language query
- Users CAN filter by language or search across all languages
- Search SHALL return ranked results by relevance
- Embeddings SHALL be regenerated on documentation update

**FR-6.4**: RAG Endpoint
- System SHALL provide `/api/v1/macros/ask` endpoint
- Users CAN ask questions in natural language
- Users CAN specify preferred language for code examples
- System SHALL return: recommended macro, example code (in preferred language), explanation
- Response SHALL cite the source macro documentation

**FR-6.5**: Macro Library UI
- Users CAN browse macro library by category and/or language
- Users CAN view full documentation for any macro
- Users CAN toggle between language-specific examples
- Users CAN search macros (keyword and semantic)
- Super admin CAN manage global macros

### FR-7: Metadata Versioning System

**FR-7.1**: Standard Version Management
- Super admin CAN create base standard versions (SDTM 3.2, ADaM 1.1, ARS 1.0)
- Each standard version SHALL have: type, version, therapeutic area, variant, effective date
- Base standards have `therapeutic_area = "general"` and `is_implementation_guide = false`
- Super admin CAN mark a version as "current" (one per type+TA per tenant)

**FR-7.2**: Therapeutic Area Implementation Guides (TA-IGs)
- Super admin CAN create TA-specific Implementation Guides (Oncology IG, CV IG, CNS IG)
- TA-IGs MUST inherit from a base standard (`parent_version_id` required)
- TA-IGs SHALL have `is_implementation_guide = true` and specific `therapeutic_area`
- TA-IGs extend base standard with TA-specific domains, variables, and codelists
- System SHALL track inheritance chain (SDTM 3.2 → SDTM-IG Oncology 1.0)
- When base standard is deprecated, system SHALL warn about dependent TA-IGs

**FR-7.3**: Variants and Amendments
- Variants track amendments within a version (e.g., COVID additions to SDTM 3.2)
- Variants inherit from same-version base and add specific changes
- Changelog SHALL document what changed between parent and variant

**FR-7.4**: Version Linkage
- Packages CAN be linked to a target standard version (base or TA-IG)
- Callables CAN be linked to standard versions they support
- Text elements CAN be versioned per standard
- System SHALL track which standard version metadata was created for

**FR-7.5**: Version History
- All versioned entities SHALL maintain change history
- Changes SHALL be logged with: timestamp, user, what changed, reason
- Users CAN view version history for any entity
- Users CAN compare versions side-by-side (future enhancement)

**FR-7.6**: Version Filtering
- Users CAN filter packages by target standard version
- Users CAN filter by therapeutic area (show only Oncology packages)
- Users CAN filter callables by supported standard versions
- When creating packages, users CAN select target standard version
- System SHALL warn if using metadata from different standard versions

**FR-7.7**: Tenant Standard Versions
- Tenants CAN import global standard versions
- Tenants CAN create tenant-specific amendments/variants
- Tenants CAN create custom TA-IGs (`therapeutic_area = "custom"`)
- Tenant versions SHALL track parent global version

### FR-8: CDISC Library Integration

**FR-8.1**: API Connection
- System SHALL connect to CDISC Library API (`https://library.cdisc.org/api`)
- API key SHALL be stored securely as environment variable
- System SHALL handle API rate limits and errors gracefully

**FR-8.2**: Standards Import
- Super admin CAN browse available CDISC products
- Super admin CAN import any SDTM, ADaM, CDASH, SEND standard/IG
- Import SHALL create StandardVersion with `external_reference` to CDISC URL
- Import SHALL preserve CDISC version numbering and metadata

**FR-8.3**: Domain/Dataset Import
- When importing an IG, system SHALL import all domains/datasets
- Each domain SHALL include: name, label, description, structure
- Each variable SHALL include: name, label, description, core, datatype, role, ordinal
- Variables SHALL preserve codelist references where applicable

**FR-8.4**: Import Mapping Algorithm

**Key Design Decision**: CDISC data is stored in dedicated tables (`cdisc_domains`, `cdisc_variables`), 
NOT directly in Package/PackageItem tables. This preserves CDISC official data integrity.

**Import Mapping Rules**:

```
CDISC Library                    →    PEARL Structure
───────────────────────────────────────────────────────────────
SDTMIG 3.4 (IG)                  →    StandardVersion (is_cdisc_official=true)
  └── Classes (Interventions)    →    Stored in domain.class_name
      └── Datasets (DM, AE)      →    CDISCDomain
          └── Variables          →    CDISCVariable
```

**StandardVersion from CDISC IG**:
| CDISC Field | Maps To |
|-------------|---------|
| href | `cdisc_href` |
| title | `display_name` |
| type ("Implementation Guide") | `is_implementation_guide = true` |
| priorVersion.href | Parent lookup for `parent_version_id` |

**CDISCDomain from CDISC Dataset**:
| CDISC Field | Maps To |
|-------------|---------|
| name | `name` (e.g., "DM") |
| label | `label` (e.g., "Demographics") |
| description | `description` |
| datasetStructure | `structure` |
| _links.parentClass.title | `class_name` |

**CDISCVariable from CDISC Variable**:
| CDISC Field | Maps To |
|-------------|---------|
| name | `name` (e.g., "USUBJID") |
| label | `label` |
| description | `description` |
| core | `core` ("Req", "Exp", "Perm") |
| simpleDatatype | `datatype` ("Char", "Num") |
| role | `role` |
| ordinal | `ordinal` |
| valueList | `value_list` (JSON array) |
| _links.codelist.href | `codelist_href` (for future CT import) |

**Tenant Package Creation from CDISC** (when user copies):
1. User selects CDISCDomain(s) to create Package from
2. System creates: Package (type=TENANT, target_standard_version_id=imported version)
3. For each selected domain:
   - Create PackageItem (type=dataset, name=domain.name)
   - Store domain variables as PackageItem metadata (or separate table)
4. Track lineage: Package.source_cdisc_domain_id (new FK)

**FR-8.5**: Customization After Import
- Tenants CAN copy imported CDISC domains to create tenant Packages
- Customized packages SHALL track source CDISC version via `target_standard_version_id`
- System SHALL NOT modify original CDISC imports (read-only)
- Tenant packages CAN add/modify/delete items; source CDISC remains unchanged

**FR-8.6**: Import UI
- Super admin portal SHALL show "Import from CDISC" action
- Browse available products, versions, Implementation Guides
- Preview import before confirming
- Show import progress and results

---

## 5. Data Model Specification

### 5.1 Package Model Changes

**Current Model** (`packages` table):
```
id: int (PK)
tenant_id: int (FK, NOT NULL)
package_name: str
created_at: datetime
updated_at: datetime
```

**New Model** (`packages` table):
```
id: int (PK)
tenant_id: int (FK, NULLABLE) -- NULL for STANDARD packages
package_name: str
package_type: enum('STANDARD', 'TENANT', 'STUDY') DEFAULT 'TENANT'
base_package_id: int (FK to packages, NULLABLE) -- inheritance tracking
study_id: int (FK to studies, NULLABLE) -- only for STUDY type
created_at: datetime
updated_at: datetime
created_by_id: int (FK to users, NULLABLE) -- who created TENANT/STUDY packages
created_by_super_admin_id: int (FK to super_admins, NULLABLE) -- who created STANDARD packages
```

**Note on Creator Fields**: 
- `created_by_id` references `users` table (for TENANT/STUDY packages)
- `created_by_super_admin_id` references `super_admins` table (for STANDARD packages)
- Exactly one should be non-NULL based on package_type

### 5.2 Constraints

**Check Constraints**:
```sql
-- STANDARD: no tenant, no study, created by super admin
CHECK (package_type != 'STANDARD' OR (
  tenant_id IS NULL AND 
  study_id IS NULL AND 
  created_by_super_admin_id IS NOT NULL AND
  created_by_id IS NULL
))

-- TENANT: has tenant, no study, created by user
CHECK (package_type != 'TENANT' OR (
  tenant_id IS NOT NULL AND 
  study_id IS NULL AND
  created_by_id IS NOT NULL AND
  created_by_super_admin_id IS NULL
))

-- STUDY: has tenant and study, created by user
CHECK (package_type != 'STUDY' OR (
  tenant_id IS NOT NULL AND 
  study_id IS NOT NULL AND
  created_by_id IS NOT NULL AND
  created_by_super_admin_id IS NULL
))

-- No self-reference
CHECK (base_package_id != id)

-- Inheritance rules: STANDARD can't inherit, others inherit from STANDARD only
CHECK (
  (package_type = 'STANDARD' AND base_package_id IS NULL) OR
  (package_type != 'STANDARD' AND (
    base_package_id IS NULL OR 
    base_package_id IN (SELECT id FROM packages WHERE package_type = 'STANDARD')
  ))
)
```

**Partial Unique Indexes** (PostgreSQL requires CREATE INDEX syntax for partial constraints):
```sql
-- Package name unique for STANDARD packages (global)
CREATE UNIQUE INDEX idx_packages_name_standard 
ON packages(package_name) 
WHERE package_type = 'standard';

-- Package name unique per tenant for TENANT packages
CREATE UNIQUE INDEX idx_packages_name_tenant 
ON packages(tenant_id, package_name) 
WHERE package_type = 'tenant';

-- Package name unique per study for STUDY packages
CREATE UNIQUE INDEX idx_packages_name_study 
ON packages(study_id, package_name) 
WHERE package_type = 'study';
```

### 5.3 RLS Policy Changes

**Current Policy**:
```sql
CREATE POLICY package_tenant_isolation ON packages
FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::int);
```

**New Policy**:
```sql
-- Read policy: tenant's packages OR standard packages
-- Note: STUDY package study-level access is enforced in CRUD layer, not RLS
CREATE POLICY package_read_policy ON packages
FOR SELECT USING (
  package_type = 'STANDARD' OR
  tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
);

-- Write policy: only tenant's packages (TENANT and STUDY types)
-- STANDARD packages are managed via super admin bypass (see 5.4)
CREATE POLICY package_write_policy ON packages
FOR INSERT, UPDATE, DELETE USING (
  tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
);
```

### 5.4 Super Admin RLS Bypass Mechanism

**Problem**: STANDARD packages have `tenant_id = NULL`, so normal RLS policies block super admin write operations.

**Solution**: Use `SET LOCAL row_security = off` within super admin endpoint transactions.

**Implementation Pattern**:
```python
# In super admin package endpoints
async def create_standard_package(db: AsyncSession, package_in: PackageCreate):
    # Disable RLS for this transaction (super admin only)
    await db.execute(text("SET LOCAL row_security = off"))
    
    # Create STANDARD package (tenant_id = NULL)
    package = Package(
        package_name=package_in.package_name,
        package_type=PackageType.STANDARD,
        tenant_id=None,
        created_by_super_admin_id=current_super_admin.id
    )
    db.add(package)
    await db.commit()
    
    # RLS automatically re-enabled at transaction end
    return package
```

**Security Notes**:
- `SET LOCAL` only affects the current transaction
- Super admin endpoints already require separate JWT authentication
- Audit logging captures all super admin operations
- Never use `SET row_security = off` (session-level) - always use `SET LOCAL`

### 5.5 STUDY Package Access Control

**RLS vs Application Layer**: RLS handles tenant isolation; application layer handles study-level access.

**CRUD Layer Enforcement** (for STUDY packages):
```python
# In package CRUD
async def get_package(db: AsyncSession, package_id: int, current_user: User):
    package = await db.get(Package, package_id)
    
    # RLS already filtered by tenant, but check study access
    if package.package_type == PackageType.STUDY:
        # Verify user has access to this study
        study_access = await check_user_study_access(
            db, current_user.id, package.study_id
        )
        if not study_access:
            raise HTTPException(403, "No access to this study's packages")
    
    return package
```

**Rationale**: Study access logic involves joining `user_study_roles` table, which is complex to embed in RLS and would impact performance for all package queries.

### 5.6 Index Additions

```sql
CREATE INDEX idx_packages_type ON packages(package_type);
CREATE INDEX idx_packages_base_package ON packages(base_package_id) WHERE base_package_id IS NOT NULL;
CREATE INDEX idx_packages_study ON packages(study_id) WHERE study_id IS NOT NULL;
CREATE INDEX idx_packages_created_by_super_admin ON packages(created_by_super_admin_id) WHERE created_by_super_admin_id IS NOT NULL;
```

### 5.7 PackageItem Deep Copy Specification

When creating a package from a STANDARD template, all items and related data must be deep-copied to ensure data isolation.

**Copy Behavior**:

| Source Entity | Copy Behavior | New ID? | References Updated? |
|---------------|---------------|---------|---------------------|
| Package | New record with new type | Yes | N/A |
| PackageItem | New record | Yes | package_id → new package |
| PackageTlfDetails | New record | Yes | package_item_id → new item |
| PackageDatasetDetails | New record | Yes | package_item_id → new item |
| PackageItemFootnote | New record | Yes | package_item_id → new item |
| PackageItemAcronym | New record | Yes | package_item_id → new item |
| TextElement (referenced) | **Shared, NOT copied** | No | Referenced by ID |

**TextElement Sharing Rationale**:
- TextElements are tenant-scoped reference data (titles, footnotes, populations)
- STANDARD packages reference global TextElements (tenant_id = NULL)
- Copied packages should create tenant-scoped TextElements OR reference existing tenant TextElements
- **Decision**: On copy, system checks if equivalent TextElement exists in target tenant:
  - If exists: Reference existing tenant TextElement
  - If not: Create new tenant-scoped copy of the TextElement

**Copy Algorithm** (pseudo-code):
```
function copyPackageFromStandard(sourcePackageId, targetType, targetTenantId, targetStudyId):
    sourcePackage = getPackage(sourcePackageId)
    
    # Create new package
    newPackage = createPackage(
        name = sourcePackage.name,  # User can override
        type = targetType,
        tenant_id = targetTenantId,
        study_id = targetStudyId,
        base_package_id = sourcePackageId  # Track lineage
    )
    
    # Copy each item
    for sourceItem in sourcePackage.items:
        newItem = copyPackageItem(sourceItem, newPackage.id, targetTenantId)
    
    return newPackage

function copyPackageItem(sourceItem, newPackageId, targetTenantId):
    # Create new item
    newItem = createPackageItem(
        package_id = newPackageId,
        item_type = sourceItem.item_type,
        item_subtype = sourceItem.item_subtype,
        item_code = sourceItem.item_code
    )
    
    # Copy type-specific details
    if sourceItem.tlf_details:
        copyTlfDetails(sourceItem.tlf_details, newItem.id, targetTenantId)
    if sourceItem.dataset_details:
        copyDatasetDetails(sourceItem.dataset_details, newItem.id)
    
    # Copy footnotes and acronyms (resolve TextElement references)
    for footnote in sourceItem.footnotes:
        resolvedTextElementId = resolveTextElement(footnote.text_element_id, targetTenantId)
        createPackageItemFootnote(newItem.id, resolvedTextElementId, footnote.sequence)
    
    return newItem

function resolveTextElement(sourceTextElementId, targetTenantId):
    sourceTE = getTextElement(sourceTextElementId)
    
    # Look for equivalent in target tenant
    existingTE = findTextElement(
        tenant_id = targetTenantId,
        type = sourceTE.type,
        label = sourceTE.label
    )
    
    if existingTE:
        return existingTE.id
    else:
        # Create tenant copy
        newTE = createTextElement(
            tenant_id = targetTenantId,
            type = sourceTE.type,
            label = sourceTE.label,
            content = sourceTE.content
        )
        return newTE.id
```

### 5.8 Audit Log Schema Update

To support STANDARD package audit logging, allow `tenant_id = NULL`:

```sql
-- Modify existing audit_log table
ALTER TABLE audit_log ALTER COLUMN tenant_id DROP NOT NULL;

-- Add index for super admin audit queries
CREATE INDEX idx_audit_log_no_tenant ON audit_log(created_at) 
WHERE tenant_id IS NULL;
```

**Audit Entry Rules**:
- STANDARD package operations: `tenant_id = NULL`
- TENANT/STUDY package operations: `tenant_id` = owning tenant
- Super admin portal shows all entries (no tenant filter)

### 5.9 Macro Library Data Model (Language-Agnostic)

**Design Notes**: 
- Language is a free-form string, not an enum, to support any programming language
- A single callable can have implementations/examples in multiple languages
- Parameter types are conceptual (data, variable) not language-specific

**pgvector Extension** (required):
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**MacroDefinition Table**:
```
macros:
- id: int (PK)
- tenant_id: int (FK, NULLABLE) -- NULL for global macros
- name: str -- "demographics", "ae_summary", "km_plot"
- display_name: str -- Human-readable: "Demographics Summary"
- languages: jsonb -- ["SAS", "R", "Python"] or ["SAS"] or ["Any"]
- category: str -- "demographics", "safety", "efficacy", "utility", "visualization"
- summary: str -- One-line description
- is_active: bool DEFAULT true
- created_at: datetime
- updated_at: datetime
- created_by_id: int (FK to users, NULLABLE)
- created_by_super_admin_id: int (FK to super_admins, NULLABLE)

Constraints:
- UNIQUE(tenant_id, name) WHERE tenant_id IS NOT NULL
- UNIQUE(name) WHERE tenant_id IS NULL
```

**MacroParameter Table** (Language-Agnostic):
```
macro_parameters:
- id: int (PK)
- macro_id: int (FK to macros)
- param_name: str -- "input_data", "treatment_var"
- param_label: str -- "Input Dataset", "Treatment Variable"
- param_type: enum('data', 'variable', 'variables', 'expression', 'literal', 'code_block', 'boolean', 'numeric', 'path')
- is_required: bool
- default_value: str (NULLABLE)
- sequence: int -- Display order
- help_text: str (NULLABLE)
- language_hints: jsonb -- {"SAS": "inds=", "R": "data=", "Python": "df="}
```

**Parameter Type Meanings** (Language-Agnostic):
| Type | Description | SAS Example | R Example | Python Example |
|------|-------------|-------------|-----------|----------------|
| data | Dataset/dataframe | ADSL | adsl | adsl_df |
| variable | Single column | USUBJID | usubjid | "usubjid" |
| variables | Multiple columns | SEX RACE AGE | c("sex", "race") | ["sex", "race"] |
| expression | Filter/condition | AGE > 18 | age > 18 | df["age"] > 18 |
| literal | String/number | "Safety" | "Safety" | "Safety" |
| code_block | Custom code | %do...%end | {...} | lambda: ... |
| boolean | True/False | Y/N | TRUE/FALSE | True/False |
| numeric | Number | 0.05 | 0.05 | 0.05 |
| path | File path | /data/out | "./data" | Path("./data") |

**MacroDocumentation Table**:
```
macro_documentation:
- id: int (PK)
- macro_id: int (FK to macros, UNIQUE)
- version: str -- "1.0.0"
- description_md: text -- Full markdown documentation
- usage_examples: jsonb -- Array of example objects WITH language tags
- use_cases: jsonb -- Array of use case descriptions
- caveats: jsonb -- Array of gotchas/limitations
- related_macro_ids: jsonb -- Array of related macro IDs
- changelog: jsonb -- Version history
- created_at: datetime
- updated_at: datetime

-- Vector embedding for RAG
- embedding: vector(1536) -- OpenAI ada-002 dimension
- embedding_model: str -- "text-embedding-ada-002"
- embedded_at: datetime
```

**Usage Example Structure** (JSON with language tags):
```json
{
  "title": "Basic Demographics",
  "description": "Standard safety demographics table",
  "output_description": "Table 14.1.1 format",
  "implementations": [
    {
      "language": "SAS",
      "code": "%demographics(inds=ADSL, trtvar=TRT01PN, catvars=SEX RACE);",
      "notes": "Uses autocall macro library"
    },
    {
      "language": "R",
      "code": "demographics(data = adsl, trt_var = \"TRT01PN\", cat_vars = c(\"SEX\", \"RACE\"))",
      "notes": "Requires tidyverse and gtsummary"
    },
    {
      "language": "Python",
      "code": "demographics(df=adsl, trt_var='TRT01PN', cat_vars=['SEX', 'RACE'])",
      "notes": "Uses pandas and tableone"
    }
  ]
}
```

**Vector Search Index**:
```sql
CREATE INDEX idx_callable_docs_embedding ON callable_documentation 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

**Vector Index Tuning Guidelines**:

| Data Size | Recommended `lists` | Notes |
|-----------|---------------------|-------|
| < 1,000 callables | 30-50 | Initial deployment |
| 1,000-10,000 | 100 | Medium scale |
| 10,000-100,000 | 316 (`sqrt(n)`) | Large scale |
| > 100,000 | Consider HNSW index | Better recall at scale |

**Production Note**: Monitor query latency. If search takes > 100ms with < 1000 callables, 
the index may need rebuilding: `REINDEX INDEX idx_callable_docs_embedding;`

**RAG Search Scope** (Multi-Tenant):

When tenant user calls `/callables/ask`:
1. Search includes: Global callables + tenant's own callables
2. Excluded: Other tenants' callables
3. Ranking: 
   - Cosine similarity (primary factor)
   - Tenant's own callables receive 10% relevance boost
   - Filter: `is_active = true` only

**Search Query**:
```sql
SELECT c.*, 
       1 - (cd.embedding <=> query_embedding) as similarity,
       CASE WHEN c.tenant_id = :current_tenant_id THEN 0.1 ELSE 0 END as boost
FROM callables c
JOIN callable_documentation cd ON c.id = cd.callable_id
WHERE (c.tenant_id IS NULL OR c.tenant_id = :current_tenant_id)
  AND c.is_active = true
ORDER BY (1 - (cd.embedding <=> query_embedding)) + boost DESC
LIMIT 10;
```

**RLS for Callables**:
```sql
-- Read: global macros OR tenant's macros
CREATE POLICY macro_read_policy ON macros
FOR SELECT USING (
  tenant_id IS NULL OR
  tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
);

-- Write: only tenant's macros (globals via super admin bypass)
CREATE POLICY macro_write_policy ON macros
FOR INSERT, UPDATE, DELETE USING (
  tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
);
```

### 5.9.1 Study Document Management Data Model

**Design Philosophy**: Study-level documents (SAP, Protocol, CRF) are uploaded per study with optional 
vectorization for RAG queries. Shares pgvector infrastructure with Callable Library for efficiency.

**StudyDocumentType Enum**:
```
enum StudyDocumentType {
  SAP = "sap"                    // Statistical Analysis Plan
  PROTOCOL = "protocol"          // Study Protocol
  CRF = "crf"                    // Case Report Form
  ANNOTATED_CRF = "annotated_crf" // Annotated CRF with SDTM mappings
  MOCK_SHELLS = "mock_shells"    // Mock TLF Shells
  OTHER = "other"                // Other study documentation
}
```

**StudyDocument Table**:
```
study_documents:
- id: int (PK)
- tenant_id: int (FK to tenants, NOT NULL)
- study_id: int (FK to studies, NOT NULL)
- document_type: enum StudyDocumentType
- document_name: str -- "STUDY-001 SAP v2.0"
- file_name: str -- "STUDY001_SAP_v2.0.pdf"
- file_path: str -- Storage path (S3 or local)
- file_size_bytes: int
- mime_type: str -- "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
- version: str -- "2.0", "1.1"
- description: text (NULLABLE)
- is_vectorized: bool DEFAULT false
- vectorized_at: datetime (NULLABLE)
- vectorization_status: enum('pending', 'processing', 'completed', 'failed') (NULLABLE)
- vectorization_error: text (NULLABLE)
- uploaded_by_id: int (FK to users)
- created_at: datetime
- updated_at: datetime

Indexes:
- idx_study_docs_study_id ON study_documents(study_id)
- idx_study_docs_tenant_id ON study_documents(tenant_id)
- idx_study_docs_type ON study_documents(document_type)
- idx_study_docs_vectorized ON study_documents(is_vectorized) WHERE is_vectorized = true
```

**StudyDocumentChunk Table** (for vectorized documents):
```
study_document_chunks:
- id: int (PK)
- document_id: int (FK to study_documents, ON DELETE CASCADE)
- chunk_index: int -- Order within document
- chunk_text: text -- Raw text content
- embedding: vector(1536) -- OpenAI embedding
- page_number: int (NULLABLE) -- For PDFs
- section_title: str (NULLABLE) -- Extracted section header
- created_at: datetime

Indexes:
- idx_doc_chunks_document_id ON study_document_chunks(document_id)
- idx_doc_chunks_embedding ON study_document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)

Note: Chunk size ~1000 tokens with 100 token overlap for context continuity.
```

**Supported File Formats**:
| Format | MIME Type | Parser |
|--------|-----------|--------|
| PDF | application/pdf | PyMuPDF or pdfplumber |
| Word | application/vnd.openxmlformats-officedocument.wordprocessingml.document | python-docx |
| Excel | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | openpyxl |
| Text | text/plain | Native |
| Markdown | text/markdown | Native (read as text) |

**Document Validation Rules**:
```python
# Configuration (in config.py)
MAX_DOCUMENT_SIZE_MB: int = Field(default=50)           # Per document
MAX_STORAGE_PER_STUDY_MB: int = Field(default=500)      # Per study total
MAX_STORAGE_PER_TENANT_GB: int = Field(default=10)      # Per tenant total
ALLOWED_EXTENSIONS: list = ['.pdf', '.docx', '.xlsx', '.txt', '.md']
```

**Validation Error Messages**:
| Scenario | HTTP Status | Error Message |
|----------|-------------|---------------|
| File too large | 400 | "Document exceeds maximum size of {MAX_DOCUMENT_SIZE_MB}MB" |
| Study quota exceeded | 400 | "Study storage quota ({MAX_STORAGE_PER_STUDY_MB}MB) exceeded" |
| Tenant quota exceeded | 400 | "Tenant storage quota ({MAX_STORAGE_PER_TENANT_GB}GB) exceeded" |
| Invalid file type | 400 | "File type not allowed. Supported: PDF, Word, Excel, TXT, Markdown" |
| Empty file | 400 | "Cannot upload empty file" |

**File Storage Strategy**:

```python
# Configuration (in config.py)
STORAGE_BACKEND: str = Field(default="local")  # "local" | "s3"
LOCAL_UPLOAD_PATH: str = Field(default="./uploads/documents")

# S3/MinIO Configuration (when STORAGE_BACKEND=s3)
S3_BUCKET: str = Field(default="pearl-documents")
S3_ACCESS_KEY: str = Field(default="")
S3_SECRET_KEY: str = Field(default="")
S3_ENDPOINT_URL: str = Field(default="")  # For S3-compatible services (MinIO, R2)
S3_REGION: str = Field(default="us-east-1")
```

**Storage Path Structure**:
```
{storage_root}/
  {tenant_id}/
    {study_id}/
      {document_id}_{filename}
      
Example: 
  uploads/documents/5/123/456_STUDY001_SAP_v2.0.pdf
  s3://pearl-documents/5/123/456_STUDY001_SAP_v2.0.pdf
```

**Storage Service Interface**:
```python
class StorageService(ABC):
    async def upload(self, file: UploadFile, path: str) -> str
    async def download(self, path: str) -> AsyncIterator[bytes]
    async def delete(self, path: str) -> bool
    async def get_size(self, tenant_id: int) -> int  # For quota tracking
```

**Audit Logging for Study Documents**:

All document operations MUST be logged to audit trail:

| Action | Logged Fields |
|--------|---------------|
| CREATE (upload) | document_id, study_id, file_name, file_size, document_type |
| UPDATE (metadata) | document_id, changed_fields |
| UPDATE (vectorize) | document_id, is_vectorized, vectorization_status |
| DELETE | document_id, file_name |

**Implementation Pattern** (in CRUD layer):
```python
async def create_document(self, db, study_id, file, ..., current_user, request):
    # ... create document ...
    
    await audit_log.log_action(
        db,
        table_name="study_documents",
        record_id=document.id,
        action="CREATE",
        user_id=current_user.id,
        changes={
            "document_name": document.document_name,
            "file_name": document.file_name,
            "file_size_bytes": document.file_size_bytes,
            "study_id": study_id
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
```

**RLS for Study Documents**:
```sql
-- Read: user must have access to the study
CREATE POLICY study_doc_read_policy ON study_documents
FOR SELECT USING (
  tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
  AND study_id IN (
    SELECT study_id FROM user_study_roles 
    WHERE user_id = NULLIF(current_setting('app.current_user_id', true), '')::int
  )
);

-- Write: user must be admin or LEAD for the study
CREATE POLICY study_doc_write_policy ON study_documents
FOR INSERT, UPDATE, DELETE USING (
  tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
);
-- Note: Additional CRUD layer check for study role
```

**Document Processing Pipeline**:
```
1. Upload: File stored to configured storage (local/S3)
2. Parse: Extract text based on MIME type
3. Chunk: Split into ~1000 token chunks with overlap
4. Embed: Generate embeddings via OpenAI
5. Store: Save chunks with embeddings to study_document_chunks
6. Index: pgvector indexes automatically update
```

**RAG Search Scope Options**:
```python
class DocumentSearchScope(str, Enum):
    SINGLE_STUDY = "single_study"      # Search within one study
    ALL_ACCESSIBLE = "all_accessible"  # Search all studies user can access
    UNIFIED = "unified"                # Search documents + callables together
```

### 5.10 Metadata Versioning Data Model

**Design Philosophy**: Standards have a hierarchical structure:
1. **Base Standards** (SDTM 3.2, ADaM 1.1) - Core model definitions
2. **Therapeutic Area Implementation Guides (TA-IGs)** - Extend base standards for specific domains
3. **Variants/Amendments** - Updates within a version (e.g., COVID additions)

This mirrors CDISC's actual structure where Oncology IG, Cardiovascular IG, etc. inherit from base SDTM.

**StandardType Enum**:
```
enum StandardType {
  SDTM = "sdtm"       // Study Data Tabulation Model
  ADAM = "adam"       // Analysis Data Model  
  ARS = "ars"         // Analysis Results Standard
  DEFINE = "define"   // Define-XML
  SEND = "send"       // Standard for Exchange of Nonclinical Data
  CUSTOM = "custom"   // Tenant-defined standards
}
```

**TherapeuticArea Table** (Lookup table for runtime extensibility):

**Design Note**: Using a lookup table instead of enum allows super admin to add new 
therapeutic areas at runtime without code deployment.

```
therapeutic_areas:
- id: int (PK)
- code: str UNIQUE -- "oncology", "cardiovascular"
- display_name: str -- "Oncology / Cancer", "Cardiovascular / Heart"
- description: text (NULLABLE)
- is_system: bool DEFAULT true -- true for CDISC-defined, false for custom
- is_active: bool DEFAULT true
- created_at: datetime
- created_by_super_admin_id: int (FK, NULLABLE)

Initial Seed Data:
| code | display_name | is_system |
|------|--------------|-----------|
| general | General (No specific TA) | true |
| oncology | Oncology / Cancer | true |
| cardiovascular | Cardiovascular / Heart | true |
| cns | Central Nervous System | true |
| vaccines | Vaccines / Immunology | true |
| rare_diseases | Rare Diseases | true |
| diabetes | Diabetes / Metabolic | true |
| respiratory | Respiratory | true |
| dermatology | Dermatology | true |
| ophthalmology | Ophthalmology | true |
```

**API Endpoints for TA Management**:
- `GET /api/v1/therapeutic-areas/` - List all TAs
- `POST /api/v1/super-admin/therapeutic-areas/` - Create custom TA
- `PUT /api/v1/super-admin/therapeutic-areas/{id}` - Update TA
- `DELETE /api/v1/super-admin/therapeutic-areas/{id}` - Deactivate TA (soft delete)

**StandardVersion Table**:
```
standard_versions:
- id: int (PK)
- tenant_id: int (FK, NULLABLE) -- NULL for global standards
- standard_type: enum StandardType
- version: str -- "3.2", "1.1", "1.0"
- therapeutic_area: enum TherapeuticArea DEFAULT "general"
- variant: str DEFAULT "base" -- "base", "covid", "2024-update"
- is_implementation_guide: bool DEFAULT false -- True for TA-specific IGs
- display_name: str -- "SDTM 3.2", "SDTM-IG Oncology 1.0 (based on SDTM 3.3)"
- description: text
- effective_date: date
- deprecated_date: date (NULLABLE) -- When this version was superseded
- parent_version_id: int (FK to standard_versions, NULLABLE) -- Lineage/inheritance
- changelog: jsonb -- What changed from parent
- external_reference: str (NULLABLE) -- CDISC URL, NCI code
- is_current: bool DEFAULT false -- Current recommended version
- created_at: datetime
- updated_at: datetime
- created_by_super_admin_id: int (FK, NULLABLE) -- For global standards

Constraints:
- UNIQUE(tenant_id, standard_type, version, therapeutic_area, variant) WHERE tenant_id IS NOT NULL
- UNIQUE(standard_type, version, therapeutic_area, variant) WHERE tenant_id IS NULL
- Only one is_current=true per (tenant_id, standard_type, therapeutic_area)
```

**Inheritance Hierarchy**:
```
SDTM 3.2 (base, general)
├── SDTM 3.2 (covid, general)        -- Amendment to base
├── SDTM-IG Oncology 1.0 (3.2)       -- Oncology IG inheriting from 3.2
│   └── SDTM-IG Oncology 1.0 (custom)-- Tenant customization
└── SDTM-IG Cardiovascular 1.0 (3.2) -- CV IG inheriting from 3.2

SDTM 3.3 (base, general)
├── SDTM-IG Oncology 1.1 (3.3)       -- Oncology IG inheriting from 3.3
└── SDTM-IG CNS 1.0 (3.3)            -- CNS IG inheriting from 3.3
```

**Example Standard Versions**:
```
| id | standard_type | version | therapeutic_area | is_ig | variant | display_name                    | parent_id |
|----|---------------|---------|------------------|-------|---------|----------------------------------|-----------|
| 1  | SDTM          | 3.2     | general          | false | base    | SDTM 3.2                         | NULL      |
| 2  | SDTM          | 3.2     | general          | false | covid   | SDTM 3.2 (COVID Amendment)       | 1         |
| 3  | SDTM          | 3.2     | oncology         | true  | base    | SDTM-IG Oncology 1.0 (SDTM 3.2)  | 1         |
| 4  | SDTM          | 3.2     | cardiovascular   | true  | base    | SDTM-IG Cardiovascular 1.0       | 1         |
| 5  | SDTM          | 3.3     | general          | false | base    | SDTM 3.3                         | 1         |
| 6  | SDTM          | 3.3     | oncology         | true  | base    | SDTM-IG Oncology 1.1 (SDTM 3.3)  | 5         |
| 7  | SDTM          | 3.3     | cns              | true  | base    | SDTM-IG CNS 1.0 (SDTM 3.3)       | 5         |
| 8  | ADAM          | 1.1     | general          | false | base    | ADaM 1.1                         | NULL      |
| 9  | ADAM          | 1.1     | oncology         | true  | base    | ADaM-IG Oncology 1.0             | 8         |
| 10 | ARS           | 1.0     | general          | false | base    | ARS 1.0                          | NULL      |
```

**TA-IG Inheritance Rules**:
1. TA-IGs MUST have a `parent_version_id` pointing to a base standard
2. TA-IGs inherit all metadata from parent, then add TA-specific extensions
3. When parent is deprecated, system warns about dependent IGs
4. Tenants can create custom TA-IGs by setting `therapeutic_area = "custom"`

### 5.11 CDISC Library Import Tracking

**Additional fields on StandardVersion** for CDISC imports:
```
standard_versions (additional columns):
- cdisc_href: str (NULLABLE) -- "/mdr/sdtmig/3-4"
- cdisc_title: str (NULLABLE) -- Original CDISC title
- cdisc_type: str (NULLABLE) -- "Foundational Model", "Implementation Guide"
- imported_at: datetime (NULLABLE) -- When imported from CDISC
- is_cdisc_official: bool DEFAULT false -- True if imported from CDISC
```

**CDISCDomain Table** (Imported domains/datasets):
```
cdisc_domains:
- id: int (PK)
- standard_version_id: int (FK to standard_versions)
- name: str -- "DM", "AE", "LB"
- label: str -- "Demographics", "Adverse Events"
- description: text
- structure: str -- "One record per subject"
- cdisc_href: str -- "/mdr/sdtmig/3-4/datasets/DM"
- ordinal: int
- class_name: str -- "Special-Purpose", "Events", "Findings"
- created_at: datetime
```

**CDISCVariable Table** (Imported variables):
```
cdisc_variables:
- id: int (PK)
- domain_id: int (FK to cdisc_domains)
- name: str -- "STUDYID", "USUBJID", "SEX"
- label: str -- "Study Identifier"
- description: text
- core: enum('Req', 'Exp', 'Perm') -- Required, Expected, Permissible
- datatype: str -- "Char", "Num"
- role: str -- "Identifier", "Topic", "Qualifier", "Timing"
- ordinal: int
- value_list: jsonb -- Allowed values if constrained
- codelist_href: str (NULLABLE) -- Link to controlled terminology
- cdisc_href: str -- "/mdr/sdtmig/3-4/datasets/DM/variables/STUDYID"
- created_at: datetime

Constraints:
- UNIQUE(domain_id, name)
```

**CDISCImportLog Table** (Track import operations):
```
cdisc_import_logs:
- id: int (PK)
- import_type: str -- "standard", "domain", "variable", "ct_package"
- cdisc_href: str
- status: enum('pending', 'in_progress', 'completed', 'failed')
- records_imported: int
- error_message: text (NULLABLE)
- started_at: datetime
- completed_at: datetime (NULLABLE)
- imported_by_super_admin_id: int (FK)
```

**CDISC Library API Configuration**:
```python
# Environment variables
CDISC_LIBRARY_API_KEY: str  # Required for imports
CDISC_LIBRARY_BASE_URL: str = "https://library.cdisc.org/api"
```

**Updates to Existing Tables** (Add standard_version_id):

```sql
-- Packages can target a standard version
ALTER TABLE packages ADD COLUMN target_standard_version_id INT REFERENCES standard_versions(id);

-- Callables can support multiple standard versions (many-to-many)
CREATE TABLE callable_standard_versions (
  callable_id INT REFERENCES callables(id) ON DELETE CASCADE,
  standard_version_id INT REFERENCES standard_versions(id) ON DELETE CASCADE,
  notes TEXT, -- How this callable applies to this version
  PRIMARY KEY (callable_id, standard_version_id)
);

-- Text elements can be version-specific
ALTER TABLE text_elements ADD COLUMN standard_version_id INT REFERENCES standard_versions(id);
```

**MetadataVersionHistory Table** (Generic change tracking):
```
metadata_version_history:
- id: int (PK)
- entity_type: str -- "package", "callable", "text_element", "package_item"
- entity_id: int
- version_number: int -- Auto-incrementing per entity
- changes: jsonb -- What changed
- reason: str (NULLABLE) -- Why it changed
- created_at: datetime
- created_by_id: int (FK to users, NULLABLE)
- created_by_super_admin_id: int (FK, NULLABLE)
```

**RLS for Standard Versions**:
```sql
-- Read: global standards OR tenant's standards
CREATE POLICY standard_version_read_policy ON standard_versions
FOR SELECT USING (
  tenant_id IS NULL OR
  tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
);
```

### 5.11 Callable Model Refinement (Multi-Language Support)

**Renamed**: `macros` table renamed to `callables` to be language-agnostic.

**Key Concept**: A "callable" represents a reusable code unit (macro, function, procedure)
that can have implementations in multiple programming languages.

**Updated Callables Table**:
```
callables:
- id: int (PK)
- tenant_id: int (FK, NULLABLE) -- NULL for global callables
- name: str -- "demographics", "ae_summary" (no language prefix)
- display_name: str -- "Demographics Summary"
- category: str -- "demographics", "safety", "efficacy", "utility"
- summary: str
- is_active: bool DEFAULT true
- created_at: datetime
- updated_at: datetime
- created_by_id: int (FK to users, NULLABLE)
- created_by_super_admin_id: int (FK, NULLABLE)
```

**CallableImplementation Table** (Language-specific details):
```
callable_implementations:
- id: int (PK)
- callable_id: int (FK to callables)
- language: str -- "SAS", "R", "Python", "Julia", etc.
- call_syntax: str -- How to invoke: "%{name}(...)", "{name}(...)", etc.
- library_requirement: str (NULLABLE) -- "tidyverse", "pandas", etc.
- notes: text (NULLABLE)
- is_active: bool DEFAULT true

Constraints:
- UNIQUE(callable_id, language)
```

**Updated CallableParameter Table**:
```
callable_parameters:
- id: int (PK)
- callable_id: int (FK to callables)
- param_name: str -- Language-agnostic name: "input_data", "treatment_var"
- param_label: str -- "Input Dataset", "Treatment Variable"
- param_type: enum('data', 'variable', 'variables', 'expression', 'literal', 
                   'code_block', 'boolean', 'numeric', 'path', 'callable')
- is_required: bool
- default_value: str (NULLABLE)
- sequence: int
- help_text: str (NULLABLE)
```

**ParameterLanguageMapping Table** (How params map to each language):
```
parameter_language_mappings:
- id: int (PK)
- parameter_id: int (FK to callable_parameters)
- language: str -- "SAS", "R", "Python"
- syntax: str -- "inds=", "data = ", "df="
- example_value: str -- "ADSL", "adsl", "adsl_df"
```

**Callable Flow**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Callable: "demographics"                                                │
│ Display Name: "Demographics Summary"                                    │
│ Category: "demographics"                                                │
├─────────────────────────────────────────────────────────────────────────┤
│ Parameters (Language-Agnostic):                                         │
│ ├── input_data (data, required)                                         │
│ ├── treatment_var (variable, required)                                  │
│ └── categorical_vars (variables, optional)                              │
├─────────────────────────────────────────────────────────────────────────┤
│ Implementations:                                                        │
│ ├── SAS: call_syntax="%demographics(...)"                               │
│ ├── R: call_syntax="demographics(...)", library="gtsummary"             │
│ └── Python: call_syntax="demographics(...)", library="tableone"         │
├─────────────────────────────────────────────────────────────────────────┤
│ Parameter Mappings:                                                     │
│ ├── input_data:                                                         │
│ │   ├── SAS: "inds=" → "ADSL"                                           │
│ │   ├── R: "data = " → "adsl"                                           │
│ │   └── Python: "df=" → "adsl_df"                                       │
│ ├── treatment_var:                                                      │
│ │   ├── SAS: "trtvar=" → "TRT01PN"                                      │
│ │   ├── R: "trt_var = " → "\"TRT01PN\""                                 │
│ │   └── Python: "trt_var=" → "'TRT01PN'"                                │
│ └── ...                                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. API Contract Definitions

### 6.1 Schema Changes

**PackageType Enum**:
```
enum PackageType {
  STANDARD = "standard"
  TENANT = "tenant"
  STUDY = "study"
}
```

**Package Schema (Updated)**:
```
PackageRead {
  id: int
  tenant_id: int | null
  package_name: str
  package_type: PackageType
  base_package_id: int | null
  base_package_name: str | null  // Computed field
  study_id: int | null
  study_label: str | null  // Computed field
  created_at: datetime
  updated_at: datetime
  created_by_id: int | null
  created_by_username: str | null  // Computed field
  item_count: int  // Computed field
  is_editable: bool  // Computed based on permissions
}

PackageCreate {
  package_name: str
  package_type: PackageType = "tenant"
  study_id: int | null  // Required if type is STUDY
}

PackageCreateFromStandard {
  source_package_id: int
  package_name: str
  package_type: PackageType  // Must be TENANT or STUDY
  study_id: int | null  // Required if type is STUDY
}
```

### 6.2 New Endpoints

**GET /api/v1/packages/standards**
- Description: List all STANDARD packages
- Auth: Any authenticated user
- Response: List[PackageRead]
- Query params: search, page, page_size

**POST /api/v1/packages/create-from-standard**
- Description: Create a new package by copying a STANDARD package
- Auth: Admin (for TENANT) or Study LEAD (for STUDY)
- Request: PackageCreateFromStandard
- Response: PackageRead
- Side effects: Copies all PackageItems and related details

**GET /api/v1/packages/{id}/derived**
- Description: List packages derived from this package
- Auth: Super admin only
- Response: List[PackageRead]
- Use case: Before deleting, see what depends on it

### 6.3 Modified Endpoints

**GET /api/v1/packages/**
- Add query param: `package_type` (filter by type)
- Add query param: `include_standards` (bool, default true)
- Response includes new fields (package_type, base_package_id, etc.)

**POST /api/v1/packages/**
- Request body includes `package_type` (optional, default TENANT)
- Validation: STANDARD type requires super admin auth
- Validation: STUDY type requires study_id

**DELETE /api/v1/packages/{id}**
- New validation: Check for derived packages
- Return 400 if packages reference this as base_package_id

### 6.4 Super Admin Endpoints

**Package Endpoints**:

**POST /api/v1/super-admin/packages/**
- Description: Create STANDARD package (super admin only)
- Auth: Super admin JWT
- Request: PackageCreate with package_type=STANDARD
- Response: PackageRead
- Implementation: Uses RLS bypass (`SET LOCAL row_security = off`)

**PUT /api/v1/super-admin/packages/{id}**
- Description: Update STANDARD package
- Auth: Super admin JWT
- Validation: Only works for STANDARD packages

**DELETE /api/v1/super-admin/packages/{id}**
- Description: Delete STANDARD package
- Auth: Super admin JWT
- Validation: Check for derived packages first
- Error: "Cannot delete: {n} packages are based on this standard"

**PackageItem Endpoints** (for STANDARD packages):

**GET /api/v1/super-admin/packages/{id}/items/**
- Description: List items in a STANDARD package
- Auth: Super admin JWT
- Response: List[PackageItemRead]

**POST /api/v1/super-admin/packages/{id}/items/**
- Description: Add item to STANDARD package
- Auth: Super admin JWT
- Request: PackageItemCreate
- Response: PackageItemRead
- WebSocket: Broadcast `standard_package_item_created` to all tenants

**PUT /api/v1/super-admin/packages/{id}/items/{item_id}**
- Description: Update item in STANDARD package
- Auth: Super admin JWT
- WebSocket: Broadcast `standard_package_item_updated` to all tenants

**DELETE /api/v1/super-admin/packages/{id}/items/{item_id}**
- Description: Delete item from STANDARD package
- Auth: Super admin JWT
- WebSocket: Broadcast `standard_package_item_deleted` to all tenants

### 6.5 WebSocket Cross-Tenant Broadcasting

**Problem**: STANDARD package changes need to notify ALL tenants, not just the current tenant.

**New WebSocket Message Types**:

**Standard Packages** (cross-tenant):

| Message Type | When Sent | Recipients |
|--------------|-----------|------------|
| `standard_package_created` | Super admin creates STANDARD | All tenants |
| `standard_package_updated` | Super admin updates STANDARD | All tenants |
| `standard_package_deleted` | Super admin deletes STANDARD | All tenants |
| `standard_package_item_created` | Item added to STANDARD | All tenants |
| `standard_package_item_updated` | Item modified in STANDARD | All tenants |
| `standard_package_item_deleted` | Item removed from STANDARD | All tenants |

**Callables** (cross-tenant for global, tenant-scoped for tenant callables):

| Message Type | When Sent | Recipients |
|--------------|-----------|------------|
| `global_callable_created` | Super admin creates global callable | All tenants |
| `global_callable_updated` | Super admin updates global callable | All tenants |
| `global_callable_deleted` | Super admin deletes global callable | All tenants |
| `callable_created` | Tenant admin creates callable | Same tenant |
| `callable_updated` | Tenant admin updates callable | Same tenant |
| `callable_deleted` | Tenant admin deletes callable | Same tenant |

**Standard Versions** (cross-tenant):

| Message Type | When Sent | Recipients |
|--------------|-----------|------------|
| `standard_version_created` | New global standard/TA-IG created | All tenants |
| `standard_version_updated` | Standard version updated | All tenants |
| `standard_version_deprecated` | Version marked deprecated | All tenants |
| `therapeutic_area_created` | New TA added | All tenants |

**CDISC Import** (super admin notification):

| Message Type | When Sent | Recipients |
|--------------|-----------|------------|
| `cdisc_import_started` | Import begins | Super admin clients |
| `cdisc_import_progress` | Every 10% or 100 records | Super admin clients |
| `cdisc_import_completed` | Import finishes successfully | All tenants (new data available) |
| `cdisc_import_failed` | Import fails | Super admin clients |

**Implementation**:

```python
# New method in WebSocket manager
async def broadcast_to_all_tenants(self, message: dict):
    """Broadcast message to all connected clients across all tenants."""
    for connection in self.active_connections:
        await connection.send_json(message)

# Usage in super admin endpoints
async def create_standard_package(...):
    package = await crud.create_standard_package(db, package_in)
    
    # Broadcast to ALL tenants
    await websocket_manager.broadcast_to_all_tenants({
        "type": "standard_package_created",
        "data": PackageRead.model_validate(package).model_dump(mode='json')
    })
    
    return package
```

**Frontend Handling**:
```typescript
// In useWebSocketRefresh hook, listen for standard package events
useWebSocketRefresh([
  'package_',           // Existing tenant-scoped events
  'standard_package_'   // New global events
], refetchPackages);
```

### 6.6 Error Messages and Deletion Protection

**Package Errors**:

| Scenario | HTTP Status | Error Message |
|----------|-------------|---------------|
| Delete STANDARD with dependents | 400 | "Cannot delete: {n} packages are based on this standard" |
| Edit STANDARD as non-super-admin | 403 | "Standard packages can only be modified by platform administrators" |
| Invalid inheritance chain | 400 | "Packages can only inherit from standard packages" |
| Create STUDY without study_id | 400 | "Study ID is required for study-scoped packages" |
| STUDY access denied | 403 | "You do not have access to this study's packages" |
| STANDARD already exists | 400 | "A standard package with this name already exists" |

**Deletion Protection Rules** (All Entities):

| Entity | Cannot Delete If | Error Message |
|--------|------------------|---------------|
| StandardVersion | Packages target this version | "Cannot delete: {n} packages target this standard version" |
| StandardVersion | TA-IGs inherit from this version | "Cannot delete: {n} implementation guides inherit from this version" |
| StandardVersion | Callables linked to this version | "Cannot delete: {n} callables reference this standard version" |
| Callable | Has active implementations | "Cannot delete callable with active implementations. Remove implementations first." |
| CallableImplementation | Documentation has examples in this language | "Cannot delete: documentation contains {n} examples in {language}. Remove examples first or use force=true to cascade delete." |
| TherapeuticArea | TA-IGs exist with this area | "Cannot delete: {n} implementation guides use this therapeutic area" |
| CDISCDomain | N/A - Read-only | "CDISC imported domains cannot be deleted" |
| CDISCVariable | N/A - Read-only | "CDISC imported variables cannot be deleted" |

**Deprecation vs Deletion**:

For entities that shouldn't be deleted but need to be "removed":
- `StandardVersion`: Set `deprecated_date` and `is_current = false`
- `Callable`: Set `is_active = false`
- `TherapeuticArea`: Set `is_active = false`

**Deprecation Cascade Behavior**:
- When StandardVersion is deprecated: System logs warning, no automatic cascade
- UI shows warning: "This version is deprecated. {n} packages and {m} callables still reference it."
- Tenant packages targeting deprecated version: Continue to work, UI shows deprecation badge

### 6.7 Feature Flags

**All feature flags** (for independent phased rollout):

```python
# In config.py
ENABLE_STANDARD_PACKAGES: bool = Field(default=False)    # Core standard packages
ENABLE_CALLABLE_LIBRARY: bool = Field(default=False)     # Callable/RAG features
ENABLE_STUDY_DOCUMENTS: bool = Field(default=False)      # Study document upload + RAG
ENABLE_METADATA_VERSIONING: bool = Field(default=False)  # Standard versions/TA-IGs
ENABLE_CDISC_IMPORT: bool = Field(default=False)         # CDISC Library integration
```

**Flag Dependencies**:
- `ENABLE_CDISC_IMPORT` requires `ENABLE_METADATA_VERSIONING` = True
- `ENABLE_STUDY_DOCUMENTS` can work independently (shares RAG with CALLABLE_LIBRARY if both enabled)
- `ENABLE_METADATA_VERSIONING` can work independently
- `ENABLE_CALLABLE_LIBRARY` can work independently
- `ENABLE_STANDARD_PACKAGES` is the core flag

**Behavior by Feature**:

| Feature | Flag | When Disabled |
|---------|------|---------------|
| Standard Packages | `ENABLE_STANDARD_PACKAGES` | `/packages/standards` returns empty list, super admin package endpoints return 404 |
| Callable Library | `ENABLE_CALLABLE_LIBRARY` | `/callables/*` endpoints return 404, RAG features hidden |
| Study Documents | `ENABLE_STUDY_DOCUMENTS` | `/studies/{id}/documents/*` returns 404, Documents tab hidden |
| Metadata Versioning | `ENABLE_METADATA_VERSIONING` | `/standard-versions/*` returns 404, version selectors hidden |
| CDISC Import | `ENABLE_CDISC_IMPORT` | `/super-admin/cdisc/*` returns 404, import UI hidden |

**Unified Search Behavior**:
- `/unified/ask` requires at least one of `ENABLE_CALLABLE_LIBRARY` or `ENABLE_STUDY_DOCUMENTS`
- Searches only enabled sources (callables if enabled, documents if enabled)
- If both disabled, returns 404

**Recommended Rollout Order**:
1. `ENABLE_STANDARD_PACKAGES` - Core feature
2. `ENABLE_METADATA_VERSIONING` - Add version tracking
3. `ENABLE_CDISC_IMPORT` - Import official standards
4. `ENABLE_CALLABLE_LIBRARY` - Add callable RAG features
5. `ENABLE_STUDY_DOCUMENTS` - Add document RAG features

**Implementation**:
```python
# In config.py
ENABLE_STANDARD_PACKAGES: bool = Field(default=False)

# In endpoint
@router.get("/standards")
async def get_standards(...):
    if not settings.ENABLE_STANDARD_PACKAGES:
        return []  # or raise 404
    ...
```

### 6.8 Standard Version API Endpoints

**Tenant Endpoints** (read global + tenant versions):

**GET /api/v1/standard-versions/**
- Description: List all standard versions (global + tenant's)
- Query params: 
  - type (sdtm, adam, ars)
  - therapeutic_area (general, oncology, cardiovascular, etc.)
  - is_implementation_guide (true/false)
  - is_current (true/false)
  - include_deprecated (true/false)
- Response: List[StandardVersionRead]

**GET /api/v1/standard-versions/{id}**
- Description: Get standard version details with changelog
- Response: StandardVersionReadFull

**GET /api/v1/standard-versions/{id}/children**
- Description: Get versions derived from this version (variants + TA-IGs)
- Response: List[StandardVersionRead]

**GET /api/v1/standard-versions/{id}/inheritance-chain**
- Description: Get full inheritance chain up to root
- Response: List[StandardVersionRead] (ordered from root to current)

**GET /api/v1/standard-versions/therapeutic-areas**
- Description: List available therapeutic areas
- Response: List[TherapeuticAreaInfo]

**POST /api/v1/standard-versions/**
- Description: Create tenant-specific amendment/variant/TA-IG
- Auth: Admin
- Request: StandardVersionCreate (must have parent_version_id for tenant versions)
- Response: StandardVersionRead

**Super Admin Endpoints** (manage global standards):

**POST /api/v1/super-admin/standard-versions/**
- Description: Create global standard version (base or TA-IG)
- Auth: Super admin JWT
- Request: StandardVersionCreate
- Response: StandardVersionRead

**POST /api/v1/super-admin/standard-versions/ta-ig**
- Description: Create Therapeutic Area Implementation Guide
- Auth: Super admin JWT
- Request: TAIGCreate (requires parent_version_id to base standard)
- Validation: Parent must be base standard (is_implementation_guide = false)

**PUT /api/v1/super-admin/standard-versions/{id}**
- Description: Update global standard version
- Auth: Super admin JWT

**DELETE /api/v1/super-admin/standard-versions/{id}**
- Description: Delete global standard version
- Validation: Check for dependent packages, callables
- Auth: Super admin JWT

**POST /api/v1/super-admin/standard-versions/{id}/set-current**
- Description: Mark version as current for its type
- Auth: Super admin JWT

### 6.9 CDISC Library Import Endpoints

**Browse CDISC Library**:

**GET /api/v1/super-admin/cdisc/products**
- Description: List all available CDISC products
- Auth: Super admin JWT
- Response: CDISCProductsResponse (mirrors CDISC Library API structure)

**GET /api/v1/super-admin/cdisc/standards/{type}**
- Description: List versions of a standard type (sdtm, adam, cdash, sendig)
- Auth: Super admin JWT
- Response: List[CDISCStandardInfo]

**GET /api/v1/super-admin/cdisc/preview/{path}**
- Description: Preview a CDISC resource before import
- Auth: Super admin JWT
- Path param: URL-encoded CDISC href (e.g., `mdr%2Fsdtmig%2F3-4`)
- Response: CDISCPreview (summary of what will be imported)

**Import Operations**:

**POST /api/v1/super-admin/cdisc/import/standard**
- Description: Import a CDISC standard or Implementation Guide
- Auth: Super admin JWT
- Request:
```json
{
  "cdisc_href": "/mdr/sdtmig/3-4",
  "include_domains": true,
  "include_variables": true,
  "on_conflict": "skip"  // "skip" | "update" | "error"
}
```
- Response: CDISCImportResult
- Creates: StandardVersion + CDISCDomains + CDISCVariables

**Idempotency Rules** (Critical):

| Scenario | `on_conflict` | Behavior |
|----------|---------------|----------|
| Standard not imported | any | Full import proceeds |
| Standard already imported | `skip` | Return existing, no changes, log as skipped |
| Standard already imported | `error` | Return 400: "Standard already imported" |
| Standard already imported | `update` | Update metadata, merge domains/variables |

**Update Merge Strategy** (when `on_conflict=update`):
1. StandardVersion: Update `display_name`, `description`, `changelog`
2. Domains: Add new domains, update existing (by name match)
3. Variables: Add new variables, update existing (by domain+name match)
4. Never delete: Existing data preserved, only additions/updates

**Conflict Detection**:
- Check `standard_versions.cdisc_href` for existing import
- Store `import_timestamp` to detect if CDISC has updated

**Partial Failure Recovery**:
- Import uses database transaction
- On failure: Full rollback, CDISCImportLog status = `failed`
- Resume: Re-run import with `on_conflict=update`
- Log captures: `records_attempted`, `records_imported`, `error_message`

**POST /api/v1/super-admin/cdisc/import/domain**
- Description: Import a single domain from an already-imported standard
- Auth: Super admin JWT
- Request: `{"standard_version_id": 5, "domain_name": "AE"}`
- Response: CDISCDomainRead

**GET /api/v1/super-admin/cdisc/imports**
- Description: List import history
- Auth: Super admin JWT
- Response: List[CDISCImportLog]

**Imported Data Access** (for all authenticated users):

**GET /api/v1/cdisc-domains/**
- Description: List imported CDISC domains
- Query params: standard_version_id, class_name
- Response: List[CDISCDomainRead]

**GET /api/v1/cdisc-domains/{id}**
- Description: Get domain with all variables
- Response: CDISCDomainReadFull

**GET /api/v1/cdisc-variables/**
- Description: List variables
- Query params: domain_id, core, role
- Response: List[CDISCVariableRead]

**CDISC Import Schemas**:

```
CDISCStandardInfo {
  href: str  // "/mdr/sdtmig/3-4"
  title: str  // "Study Data Tabulation Model Implementation Guide..."
  type: str  // "Implementation Guide", "Foundational Model"
  already_imported: bool  // true if exists in PEARL
  pearl_version_id: int | null  // ID if already imported
}

CDISCPreview {
  href: str
  title: str
  type: str
  domain_count: int
  variable_count: int
  classes: List[str]
  domains: List[CDISCDomainPreview]
}

CDISCDomainPreview {
  name: str  // "DM"
  label: str  // "Demographics"
  variable_count: int
}

CDISCImportResult {
  success: bool
  standard_version_id: int
  domains_imported: int
  variables_imported: int
  import_log_id: int
  errors: List[str]
}

CDISCDomainRead {
  id: int
  standard_version_id: int
  name: str
  label: str
  description: str | null
  structure: str
  class_name: str
  variable_count: int
  cdisc_href: str
}

CDISCVariableRead {
  id: int
  domain_id: int
  name: str
  label: str
  description: str | null
  core: str  // "Req", "Exp", "Perm"
  datatype: str  // "Char", "Num"
  role: str
  ordinal: int
  value_list: List[str] | null
  codelist_href: str | null
}
```

**Standard Version Schemas**:

```
StandardVersionRead {
  id: int
  tenant_id: int | null
  standard_type: str  // "sdtm", "adam", "ars"
  version: str
  therapeutic_area: str  // "general", "oncology", "cardiovascular", etc.
  variant: str
  is_implementation_guide: bool
  display_name: str
  description: str | null
  effective_date: date
  deprecated_date: date | null
  parent_version_id: int | null
  is_current: bool
  is_global: bool  // Computed: tenant_id IS NULL
  usage_count: int  // How many packages use this version
  child_count: int  // How many versions inherit from this
}

StandardVersionReadFull extends StandardVersionRead {
  changelog: dict | null
  external_reference: str | null
  parent_version: StandardVersionRead | null
  children: List[StandardVersionRead]  // Direct children only
  inheritance_chain: List[StandardVersionRead]  // Full chain to root
}

StandardVersionCreate {
  standard_type: str
  version: str
  therapeutic_area: str = "general"
  variant: str = "base"
  is_implementation_guide: bool = false
  display_name: str
  description: str | null
  effective_date: date
  parent_version_id: int | null  // Required for TA-IGs and variants
  changelog: dict | null
  external_reference: str | null
}

TAIGCreate {
  // Convenience schema for creating TA Implementation Guides
  standard_type: str
  version: str  // IG version, e.g., "1.0"
  therapeutic_area: str  // Must not be "general"
  display_name: str
  description: str | null
  effective_date: date
  parent_version_id: int  // Required: must point to base standard
  changelog: dict | null
}

TherapeuticAreaInfo {
  code: str  // "oncology"
  display_name: str  // "Oncology / Cancer"
  description: str | null
  standard_count: int  // How many IGs exist for this TA
}
```

### 6.9 Callable Library API Endpoints

**Note**: "Callable" is the language-agnostic term for macro/function/procedure.
API uses `/callables/` path for future-proofing.

**Callable CRUD Endpoints**:

**GET /api/v1/callables/**
- Description: List all callables (global + tenant's)
- Auth: Any authenticated user
- Query params: language, category, standard_version_id, search (keyword)
- Response: List[CallableRead]

**GET /api/v1/callables/{id}**
- Description: Get callable details with parameters and implementations
- Auth: Any authenticated user
- Response: CallableReadFull (includes parameters, implementations)

**POST /api/v1/callables/**
- Description: Create tenant callable
- Auth: Admin
- Request: CallableCreate
- Response: CallableRead

**PUT /api/v1/callables/{id}**
- Description: Update callable
- Auth: Admin (tenant), Super admin (global)
- Request: CallableUpdate

**DELETE /api/v1/callables/{id}**
- Description: Delete callable
- Auth: Admin (tenant), Super admin (global)

**Callable Implementation Endpoints**:

**POST /api/v1/callables/{id}/implementations/**
- Description: Add language implementation
- Request: CallableImplementationCreate
- Response: CallableImplementationRead

**PUT /api/v1/callables/{id}/implementations/{lang}**
- Description: Update language implementation
- Request: CallableImplementationUpdate

**DELETE /api/v1/callables/{id}/implementations/{lang}**
- Description: Remove language implementation

**Callable Documentation Endpoints**:

**GET /api/v1/callables/{id}/documentation**
- Description: Get full documentation
- Response: CallableDocumentationRead

**PUT /api/v1/callables/{id}/documentation**
- Description: Create/update documentation
- Request: CallableDocumentationUpdate
- Side effect: Regenerates embedding vector

**GET /api/v1/callables/{id}/examples**
- Description: Get just the usage examples
- Query params: language (optional - filter by language)
- Response: List[UsageExample]

**Search & RAG Endpoints**:

**GET /api/v1/callables/search**
- Description: Semantic search using pgvector
- Query params: 
  - q (natural language query)
  - language (optional - filter results by language)
  - standard_version_id (optional - filter by standard)
  - limit (default 10)
- Response: List[CallableSearchResult] with relevance scores
- Implementation: Converts query to embedding, cosine similarity search

**POST /api/v1/callables/ask**
- Description: RAG endpoint - natural language to callable recommendation
- Request: 
```json
{
  "question": "How do I create a demographics table?",
  "preferred_language": "R",
  "standard_version_id": 5  // optional - filter by standard
}
```
- Response:
```json
{
  "answer": "Use the demographics function for standard demographic summaries.",
  "recommended_callable": {
    "id": 123,
    "name": "demographics",
    "display_name": "Demographics Summary",
    "available_languages": ["SAS", "R", "Python"]
  },
  "example_code": "demographics(data = adsl, trt_var = \"TRT01PN\", cat_vars = c(\"SEX\", \"RACE\"))",
  "example_language": "R",
  "explanation": "This function generates Table 14.1.1 format with categorical and continuous variables. Available in SAS, R, and Python.",
  "other_languages": [
    {"language": "SAS", "code": "%demographics(inds=ADSL, trtvar=TRT01PN, catvars=SEX RACE);"},
    {"language": "Python", "code": "demographics(df=adsl, trt_var='TRT01PN', cat_vars=['SEX', 'RACE'])"}
  ],
  "sources": [
    {"callable_id": 123, "section": "usage_examples"}
  ]
}
```
- Implementation: 
  1. Convert question to embedding
  2. Search callable documentation
  3. Use LLM to generate answer with context
  4. Return examples in preferred language, with alternatives

**Super Admin Callable Endpoints**:

**POST /api/v1/super-admin/callables/**
- Description: Create global callable
- Auth: Super admin JWT

**PUT /api/v1/super-admin/callables/{id}**
- Description: Update global callable
- Auth: Super admin JWT

**DELETE /api/v1/super-admin/callables/{id}**
- Description: Delete global callable
- Auth: Super admin JWT

**Callable Schemas**:

```
CallableRead {
  id: int
  tenant_id: int | null
  name: str
  display_name: str
  category: str
  summary: str
  is_global: bool  // Computed: tenant_id IS NULL
  is_active: bool
  available_languages: List[str]  // Computed from implementations
  parameter_count: int  // Computed
  has_documentation: bool  // Computed
  supported_standard_versions: List[int]  // IDs of linked standards
}

CallableReadFull extends CallableRead {
  parameters: List[CallableParameterRead]
  implementations: List[CallableImplementationRead]
  documentation: CallableDocumentationRead | null
}

CallableImplementationRead {
  id: int
  language: str  // "SAS", "R", "Python"
  call_syntax: str  // "%{name}(...)", "{name}(...)"
  library_requirement: str | null
  notes: str | null
  is_active: bool
}

CallableParameterRead {
  id: int
  param_name: str
  param_label: str
  param_type: str  // "data", "variable", "variables", etc.
  is_required: bool
  default_value: str | null
  sequence: int
  help_text: str | null
  language_mappings: List[ParameterLanguageMapping]
}

ParameterLanguageMapping {
  language: str
  syntax: str  // "inds=", "data = ", "df="
  example_value: str
}

CallableCreate {
  name: str
  display_name: str
  category: str
  summary: str
  parameters: List[CallableParameterCreate]
  implementations: List[CallableImplementationCreate]
  standard_version_ids: List[int]  // Which standards this callable supports
}

CallableParameterCreate {
  param_name: str
  param_label: str
  param_type: str
  is_required: bool
  default_value: str | null
  sequence: int
  help_text: str | null
  language_hints: dict | null
}

CallableImplementationCreate {
  language: str
  call_syntax: str
  library_requirement: str | null
  notes: str | null
}

UsageExample {
  title: str
  description: str
  output_description: str | null
  implementations: List[LanguageImplementation]
}

LanguageImplementation {
  language: str  // "SAS", "R", "Python", etc.
  code: str
  notes: str | null
}

CallableDocumentationUpdate {
  version: str
  description_md: str
  usage_examples: List[UsageExample]
  use_cases: List[str]
  caveats: List[str]
  related_callable_ids: List[int]
}

CallableSearchResult {
  callable: CallableRead
  relevance_score: float  // 0-1, cosine similarity
  matched_section: str  // "description", "example", "use_case"
  snippet: str  // Relevant text excerpt
  available_languages: List[str]
}
```

### 6.10 Study Document Management API Endpoints

**Note**: Study documents are scoped to studies. RAG infrastructure shared with Callable Library.

**Document CRUD Endpoints**:

**GET /api/v1/studies/{study_id}/documents/**
- Description: List documents for a study
- Auth: User with study access
- Query params: document_type, is_vectorized
- Response: List[StudyDocumentRead]

**GET /api/v1/studies/{study_id}/documents/{id}**
- Description: Get document metadata
- Auth: User with study access
- Response: StudyDocumentRead

**POST /api/v1/studies/{study_id}/documents/**
- Description: Upload study document
- Auth: Admin or LEAD for study
- Request: multipart/form-data with file + metadata
- Request fields:
  - file: binary
  - document_type: enum (sap, protocol, crf, etc.)
  - document_name: str (display name)
  - version: str (optional)
  - description: str (optional)
  - vectorize: bool (default false)
- Response: StudyDocumentRead
- Behavior: If vectorize=true, starts async vectorization

**PUT /api/v1/studies/{study_id}/documents/{id}**
- Description: Update document metadata (not file)
- Auth: Admin or LEAD for study
- Request: StudyDocumentUpdate

**DELETE /api/v1/studies/{study_id}/documents/{id}**
- Description: Delete document and chunks
- Auth: Admin or LEAD for study
- Behavior: Cascades to study_document_chunks

**GET /api/v1/studies/{study_id}/documents/{id}/download**
- Description: Download original file
- Auth: User with study access
- Response: File stream with appropriate Content-Type

**Vectorization Endpoints**:

**POST /api/v1/studies/{study_id}/documents/{id}/vectorize**
- Description: Start vectorization for document
- Auth: Admin or LEAD for study
- Response: {"status": "processing", "job_id": "..."}
- Behavior:
  1. Sets vectorization_status = "processing"
  2. Queues background job to:
     a. Parse document (PDF/Word/Excel)
     b. Chunk text (~1000 tokens)
     c. Generate embeddings
     d. Store in study_document_chunks
  3. Updates status on completion/failure

**GET /api/v1/studies/{study_id}/documents/{id}/vectorization-status**
- Description: Check vectorization progress
- Response: 
```json
{
  "status": "processing" | "completed" | "failed",
  "progress_percent": 75,
  "chunks_created": 45,
  "error_message": null
}
```

**DELETE /api/v1/studies/{study_id}/documents/{id}/vectors**
- Description: Remove vectorization (keep original file)
- Auth: Admin or LEAD for study
- Behavior: Deletes chunks, sets is_vectorized=false

**Study Document RAG Endpoints**:

**GET /api/v1/studies/{study_id}/documents/search**
- Description: Semantic search within study documents
- Auth: User with study access
- Query params:
  - q: str (natural language query)
  - document_types: List[str] (optional filter)
  - limit: int (default 10)
- Response: List[DocumentSearchResult]

**POST /api/v1/studies/{study_id}/documents/ask**
- Description: RAG endpoint - ask questions about study documents
- Auth: User with study access
- Request:
```json
{
  "question": "What is the primary endpoint in this study?",
  "document_types": ["sap", "protocol"],  // optional filter
  "include_sources": true
}
```
- Response:
```json
{
  "answer": "The primary endpoint is...",
  "sources": [
    {
      "document_id": 45,
      "document_name": "STUDY-001 Protocol v2.0",
      "page_number": 12,
      "section_title": "3.1 Primary Endpoint",
      "snippet": "The primary efficacy endpoint..."
    }
  ],
  "confidence": 0.85
}
```

**Cross-Study Search Endpoints**:

**GET /api/v1/documents/search**
- Description: Search across all studies user can access
- Auth: Authenticated user
- Query params:
  - q: str
  - study_ids: List[int] (optional - filter to specific studies)
  - document_types: List[str]
  - limit: int (default 10)
- Response: List[DocumentSearchResult] (includes study_id in each result)

**POST /api/v1/documents/ask**
- Description: RAG across all accessible study documents
- Auth: Authenticated user
- Request:
```json
{
  "question": "How do similar studies handle missing data?",
  "study_ids": [1, 2, 3],  // optional - limit scope
  "document_types": ["sap"]
}
```
- Response: Same as single-study /ask but sources from multiple studies

**Unified Search Endpoint** (Documents + Callables):

**POST /api/v1/unified/ask**
- Description: Search both callables and study documents
- Auth: Authenticated user
- Request:
```json
{
  "question": "How do I generate a demographics table for this study?",
  "search_callables": true,
  "search_documents": true,
  "study_ids": [5],  // Optional - for document search
  "preferred_language": "R"
}
```
- Response:
```json
{
  "answer": "Based on your study's SAP, demographics should include...",
  "callable_results": [
    {
      "callable_id": 123,
      "name": "demographics",
      "recommended_code": "demographics(data = adsl, ...)"
    }
  ],
  "document_results": [
    {
      "document_id": 45,
      "document_name": "STUDY-001 SAP",
      "snippet": "Table 14.1.1 Demographics shall include..."
    }
  ]
}
```

**Unified Search Scope & Access Control**:
```
Search Scope Rules:
1. Callables:
   - Global callables (tenant_id IS NULL): Always included
   - Tenant callables (tenant_id = user's tenant): Included
   - Other tenants' callables: Excluded
   
2. Documents:
   - Only from studies user has access to (via user_study_roles)
   - If study_ids provided: Filter to those studies (still must have access)
   - If study_ids empty/null: Search all accessible studies
   
3. Results:
   - Combined and sorted by relevance score
   - Callable results and document results returned separately
   - LLM generates unified answer considering both sources

Access Requirements:
- Any authenticated user can call /unified/ask
- Results automatically scoped to user's permissions
- Admin users see all tenant callables + all tenant studies
- Non-admin users see global callables + tenant callables + assigned studies only
```

**Study Document Schemas**:

```
StudyDocumentRead {
  id: int
  study_id: int
  document_type: str
  document_name: str
  file_name: str
  file_size_bytes: int
  mime_type: str
  version: str | null
  description: str | null
  is_vectorized: bool
  vectorized_at: datetime | null
  vectorization_status: str | null
  chunk_count: int | null  // Computed if vectorized
  uploaded_by: UserBasic
  created_at: datetime
  updated_at: datetime
}

StudyDocumentCreate {
  document_type: str
  document_name: str
  version: str | null
  description: str | null
  vectorize: bool = false
}

StudyDocumentUpdate {
  document_name: str | null
  version: str | null
  description: str | null
}

DocumentSearchResult {
  document_id: int
  study_id: int
  document_name: str
  document_type: str
  relevance_score: float
  page_number: int | null
  section_title: str | null
  snippet: str
}
```

**WebSocket Events**:

| Event | When | Recipients |
|-------|------|------------|
| `study_document_uploaded` | Document uploaded | Study members |
| `study_document_deleted` | Document deleted | Study members |
| `study_document_vectorized` | Vectorization complete | Study members |
| `study_document_vectorization_failed` | Vectorization failed | Study admins |

---

## 7. Frontend Components

### 7.1 Component Inventory

**Standard Packages Components**:

| Component | Type | Description |
|-----------|------|-------------|
| PackageTypeSelector | Form Control | Dropdown for selecting package type |
| StandardPackagesList | Page Section | List of standard packages (read-only view) |
| PackageTypeBadge | Display | Visual indicator of package type |
| CreateFromStandardDialog | Dialog | Modal for copying standard package |
| InheritanceIndicator | Display | Shows "Based on: X" linkage |
| PackageListFilters | Control | Filter by type, search |
| StandardPackageManagement | Page | Super admin page for managing standards |

**Callable Library Components**:

| Component | Type | Description |
|-----------|------|-------------|
| CallableLibraryPage | Page | Main callable library browser |
| CallableCard | Display | Card showing callable summary + language badges |
| CallableDetailView | Page | Full callable documentation view |
| CallableSearchBar | Control | Semantic search input |
| CallableSearchResults | Display | Search results with relevance scores |
| CallableAskDialog | Dialog | RAG chat interface for questions |
| CallableParameterList | Display | Table of parameters with language mappings |
| CallableExamplesList | Display | Code examples with language tabs + copy button |
| CallableDocEditor | Form | Markdown editor for documentation |
| CallableCategoryFilter | Control | Filter by category/language/standard |
| CallableCreateDialog | Dialog | Create new callable with implementations |
| LanguageImplementationEditor | Form | Add/edit language-specific implementations |
| LanguageBadge | Display | Shows supported languages (SAS, R, Python) |

**Metadata Versioning Components**:

| Component | Type | Description |
|-----------|------|-------------|
| StandardVersionsPage | Page | Super admin page for managing standards |
| StandardVersionCard | Display | Card showing version info + lineage + TA badge |
| StandardVersionTree | Display | Visual inheritance tree (base → TA-IGs → variants) |
| StandardVersionSelector | Form Control | Dropdown with grouping by type and TA |
| StandardVersionBadge | Display | Shows standard version on packages/callables |
| TherapeuticAreaFilter | Control | Filter by therapeutic area (Oncology, CV, etc.) |
| TherapeuticAreaBadge | Display | Badge showing TA (e.g., "Oncology IG") |
| VersionHistoryDialog | Dialog | View change history for any entity |
| CreateStandardVersionDialog | Dialog | Create new standard/variant |
| CreateTAIGDialog | Dialog | Create TA Implementation Guide (inherits from base) |
| InheritanceChainView | Display | Shows full inheritance path to root |
| VersionCompareView | Display | Side-by-side version comparison (future) |

**CDISC Library Import Components**:

| Component | Type | Description |
|-----------|------|-------------|
| CDISCImportPage | Page | Super admin page for CDISC imports |
| CDISCProductBrowser | Display | Browse CDISC products (SDTM, ADaM, etc.) |
| CDISCVersionList | Display | List versions of a standard type |
| CDISCImportPreview | Dialog | Preview domains/variables before import |
| CDISCImportProgress | Display | Import progress indicator |
| CDISCImportHistory | Display | Table of past imports with status |
| CDISCDomainViewer | Page | View imported domains and variables |
| CDISCVariableTable | Display | Table of variables with core/role/datatype |
| CDISCBadge | Display | Badge showing "CDISC Official" |

### 7.2 Page Changes

**Packages Page** (`/packages`)
- Add tab or section for "Standard Packages"
- Add filter dropdown for package type
- Show PackageTypeBadge on each package card
- Add "Create from Standard" button when viewing standards
- Show InheritanceIndicator when package has base_package_id

**Package Detail Page** (`/packages/{id}`)
- Show PackageTypeBadge in header
- Show InheritanceIndicator if derived
- Disable edit controls for STANDARD packages (unless super admin)
- Add "Create Copy" action for STANDARD packages

**Super Admin Portal** (new or extend existing)
- Standard Package Management page
- CRUD operations for STANDARD packages
- View usage statistics (derived count)

### 7.3 User Flows

**Flow 1: View Standard Packages**
```
1. User navigates to Packages page
2. User clicks "Standard Packages" tab/filter
3. System displays list of STANDARD packages
4. User can view details (read-only)
5. User can click "Create from Standard" to copy
```

**Flow 2: Create Package from Standard**
```
1. User clicks "Create from Standard" on a standard package
2. Dialog opens with:
   - Source package name (read-only)
   - New package name (required)
   - Package type selector (TENANT or STUDY)
   - Study selector (if STUDY type selected)
3. User fills form and clicks "Create"
4. System creates copy with all items
5. User redirected to new package detail page
```

**Flow 3: Super Admin Creates Standard (Manual)**
```
1. Super admin navigates to Standard Package Management
2. Clicks "Create Standard Package"
3. Fills package name and metadata
4. Selects target standard version (optional)
5. Adds items to package (TLFs, datasets)
6. Publishes package (available to all tenants)
```

**Flow 4: Super Admin Creates Standard from CDISC Import**
```
1. Super admin navigates to CDISC Import page
2. Browses CDISC products, selects standard (e.g., SDTMIG 3.4)
3. Previews domains and variables to import
4. Clicks "Import"
5. System creates:
   - StandardVersion (is_cdisc_official=true)
   - CDISCDomains with all variables
6. Standard version now available as target for tenant packages
7. Tenants can copy CDISC domains to create their own Packages
```

**Flow 5: Initial Data Seeding Options**
```
Option A: CDISC Import (Recommended)
1. Deploy system
2. Super admin imports official CDISC standards via Flow 4
3. Tenants immediately have access to official standards

Option B: Manual Creation
1. Deploy system
2. Super admin manually creates STANDARD packages via Flow 3
3. More effort but allows custom standards not in CDISC

Option C: Seed Script
1. Create seed script: backend/scripts/seed_standard_packages.py
2. Script creates predefined STANDARD packages on first run
3. Useful for dev/test environments
```

### 7.4 State Management

**New Zustand Store**: `packageFilterStore`
```
{
  selectedType: PackageType | 'all'
  includeStandards: boolean
  searchTerm: string
  setSelectedType: (type) => void
  setIncludeStandards: (include) => void
  setSearchTerm: (term) => void
}
```

**API Query Keys** (TanStack Query):
```
['packages', { type, includeStandards, search }]
['packages', 'standards']
['packages', id, 'derived']
```

---

## 8. Worktree Strategy & Parallel Development

### 8.1 Worktree Overview

Git worktrees allow multiple branches to be checked out simultaneously, enabling parallel development. Each worktree operates independently but shares the same Git repository.

### 8.1.1 Database Strategy (Hybrid Approach)

**Strategy**: Group related worktrees to share databases; independent worktrees get separate DBs.

**Database Groups**:
```
pearl_core_db     → WT-1, WT-2, WT-3, WT-4 (core packages - sequential)
pearl_callable_db → WT-9 (callable library - independent)
pearl_version_db  → WT-10, WT-11 (versioning + CDISC - dependent, share DB)
pearl_frontend_db → WT-5, WT-6, WT-7 (frontend - uses merged backend)
pearl_main_db     → main branch (production-like)
```

**Environment Files**:
```bash
# backend/.env.wt_core (for WT-1 through WT-4)
DATABASE_URL=postgresql+asyncpg://postgres:pass@localhost:5432/pearl_core_db

# backend/.env.wt_callable (for WT-9)
DATABASE_URL=postgresql+asyncpg://postgres:pass@localhost:5432/pearl_callable_db

# backend/.env.wt_version (for WT-10 and WT-11)
DATABASE_URL=postgresql+asyncpg://postgres:pass@localhost:5432/pearl_version_db

# backend/.env (main branch)
DATABASE_URL=postgresql+asyncpg://postgres:pass@localhost:5432/pearl_main_db
```

**Why Hybrid**:
- Independent worktrees (WT-9 callables) can develop without affecting others
- Dependent worktrees (WT-10 → WT-11) share DB to avoid migration duplication
- Frontend worktrees use merged backend APIs, not their own migrations

### 8.1.2 Migration Merge Strategy

When merging multiple worktrees to main:

```bash
# 1. Merge first worktree (e.g., WT-10)
git checkout main
git merge feature/mdr-phase1-versioning
alembic upgrade head  # Apply WT-10 migrations to pearl_main_db

# 2. Merge second worktree (e.g., WT-9 callables)
git merge feature/mdr-phase1-callables

# 3. Check for multiple heads
alembic heads
# If two heads exist: abc123 (versioning), def456 (callables)

# 4. Create merge migration
alembic merge -m "merge versioning and callables" abc123 def456
# Creates migration with down_revision = [abc123, def456]

# 5. Apply to main DB
alembic upgrade head
```

**Before Merge Checklist**:
- [ ] Pull latest main into worktree
- [ ] Rebase migrations if main has new ones (update `down_revision`)
- [ ] Test: Drop and recreate worktree DB, run `alembic upgrade head`
- [ ] Verify model validator passes: `uv run python tests/validator/run_model_validation.py`

### 8.2 Proposed Worktrees

| Worktree | Branch | Focus Area | Database | Dependencies |
|----------|--------|------------|----------|--------------|
| WT-1: migrations | `feature/mdr-phase1-migrations` | Database schema changes | `pearl_core_db` | None (runs first) |
| WT-2: backend-models | `feature/mdr-phase1-models` | SQLAlchemy models, schemas | `pearl_core_db` | WT-1 migrations applied |
| WT-3: backend-crud | `feature/mdr-phase1-crud` | CRUD operations | `pearl_core_db` | WT-2 models defined |
| WT-4: backend-api | `feature/mdr-phase1-api` | API endpoints | `pearl_core_db` | WT-3 CRUD ready |
| WT-5: frontend-api | `feature/mdr-phase1-fe-api` | API client, types | (uses main) | WT-4 merged to main |
| WT-6: frontend-components | `feature/mdr-phase1-fe-components` | UI components | (uses main) | WT-5 API client ready |
| WT-7: frontend-pages | `feature/mdr-phase1-fe-pages` | Page integration | (uses main) | WT-6 components ready |
| WT-8: testing | `feature/mdr-phase1-testing` | Automated tests | `pearl_main_db` | All other WTs merged |
| WT-9: callables | `feature/mdr-phase1-callables` | Callable library + RAG | `pearl_callable_db` | WT-2 merged to main |
| WT-10: versioning | `feature/mdr-phase1-versioning` | Standard versions, TA-IGs | `pearl_version_db` | WT-2 merged to main |
| WT-11: cdisc-import | `feature/mdr-phase1-cdisc` | CDISC Library integration | `pearl_version_db` | WT-10 (shares DB) |

### 8.3 Dependency Graph (Complete)

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
       │                       │                       │
       │                       ▼                       ▼
       │                WT-4: backend-api       WT-11: CDISC import
       │                       │                       │
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

**Legend**:
- WT-1 to WT-8: Core Standard Packages feature
- WT-9: Callable Library (parallel track after WT-2)
- WT-10: Metadata Versioning (parallel track after WT-2)
- WT-11: CDISC Import (depends on WT-10)

### 8.4 Parallel Opportunities

**Can run in parallel** (each with separate DB):
- WT-3/WT-4 (core packages) on `pearl_core_db`
- WT-9 (callables) on `pearl_callable_db`
- WT-10/WT-11 (versioning + CDISC) on `pearl_version_db`

**Sequential dependencies**:
- WT-1 → WT-2 (must be first, establishes base schema)
- WT-2 → WT-3 → WT-4 (core backend chain)
- WT-2 merged → WT-9 branches (callable library)
- WT-2 merged → WT-10 → WT-11 (versioning → CDISC, share DB)
- WT-4 merged → WT-5 → WT-6 → WT-7 (frontend chain)
- All merged → WT-8 (testing validates everything)

**Merge order** (recommended):
1. WT-1: migrations (first - base schema)
2. WT-2: models (depends on WT-1)
3. WT-3: crud (depends on WT-2)
4. WT-4: api (depends on WT-3) → **Merge to main, creates stable backend base**
5. WT-10: versioning (can run parallel to WT-3/WT-4)
6. WT-9: callables (can run parallel to WT-3/WT-4/WT-10)
7. WT-11: CDISC import (depends on WT-10, shares DB)
8. WT-5: frontend-api (depends on merged backend)
9. WT-6: frontend-components
10. WT-7: frontend-pages
11. WT-8: testing (last, validates everything)

### 8.5 Worktree Setup Commands

```bash
# Create databases first
psql -c "CREATE DATABASE pearl_core_db;"
psql -c "CREATE DATABASE pearl_callable_db;"
psql -c "CREATE DATABASE pearl_version_db;"
psql -c "CREATE DATABASE pearl_main_db;"

# Create worktrees from main branch
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

# Setup environment files per worktree group
# Core worktrees (WT-1 to WT-4)
echo 'DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pearl_core_db' > ../pearl-wt-migrations/backend/.env
cp ../pearl-wt-migrations/backend/.env ../pearl-wt-models/backend/.env
cp ../pearl-wt-migrations/backend/.env ../pearl-wt-crud/backend/.env
cp ../pearl-wt-migrations/backend/.env ../pearl-wt-api/backend/.env

# Callable worktree (WT-9)
echo 'DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pearl_callable_db' > ../pearl-wt-callables/backend/.env

# Versioning worktrees (WT-10, WT-11 - shared DB)
echo 'DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pearl_version_db' > ../pearl-wt-versioning/backend/.env
cp ../pearl-wt-versioning/backend/.env ../pearl-wt-cdisc/backend/.env

# Initialize each database with base schema
for db in pearl_core_db pearl_callable_db pearl_version_db; do
  cd ../pearl-wt-migrations/backend
  DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/$db" uv run alembic upgrade head
done
```

### 8.6 Communication Protocol

Agents must communicate about:
1. **Migration status**: "Migrations applied, models can proceed"
2. **Interface contracts**: Share schema/type definitions
3. **Blockers**: Report any issues blocking downstream work
4. **Completion**: Notify when ready for merge

**Coordination file**: `.worktree-status.json` (in shared location)
```json
{
  "migrations": {"status": "complete", "timestamp": "..."},
  "models": {"status": "in_progress", "blocker": null},
  "crud": {"status": "waiting", "waiting_for": "models"},
  ...
}
```

---

## 9. Database Migration Strategy

### 9.1 Hybrid Database Benefits

With the hybrid database strategy (Section 8.1.1):
- Independent worktrees can run migrations without affecting each other
- Dependent worktrees (WT-10, WT-11) share a database and coordinate
- Migration conflicts are resolved at merge time using `alembic merge heads`

**Key Principle**: Each database group can evolve independently; conflicts resolved when merging to main.

### 9.2 Migration Sequencing

**Phase 1 Migrations** (must be applied in order):

| Order | Migration | Description | Reversible |
|-------|-----------|-------------|------------|
| 1 | `add_package_type_enum` | Create PackageType enum | Yes |
| 2 | `add_package_columns` | Add package_type, base_package_id, study_id, created_by_id | Yes |
| 3 | `add_package_constraints` | Add check constraints | Yes |
| 4 | `update_package_rls` | Modify RLS policies | Yes |
| 5 | `add_package_indexes` | Add performance indexes | Yes |
| 6 | `migrate_existing_packages` | Set existing packages to TENANT type | Yes |

### 9.3 Migration Files

**Migration 1: add_package_type_enum.py**
```
Revision: mdr_phase1_001
Dependencies: [latest_existing_migration]
Operations:
- Create enum type 'packagetype' with values ('standard', 'tenant', 'study')
```

**Migration 2: add_package_columns.py**
```
Revision: mdr_phase1_002
Dependencies: mdr_phase1_001
Operations:
- ALTER TABLE packages ADD COLUMN package_type packagetype DEFAULT 'tenant'
- ALTER TABLE packages ADD COLUMN base_package_id INTEGER REFERENCES packages(id)
- ALTER TABLE packages ADD COLUMN study_id INTEGER REFERENCES studies(id)
- ALTER TABLE packages ADD COLUMN created_by_id INTEGER REFERENCES users(id)
- ALTER TABLE packages ALTER COLUMN tenant_id DROP NOT NULL
```

**Migration 3: add_package_constraints.py**
```
Revision: mdr_phase1_003
Dependencies: mdr_phase1_002
Operations:
- Add check constraints for package_type logic
- Add unique constraints per type scope
```

**Migration 4: update_package_rls.py**
```
Revision: mdr_phase1_004
Dependencies: mdr_phase1_003
Operations:
- DROP existing package RLS policies
- CREATE new read policy (include STANDARD)
- CREATE new write policy (tenant only)
```

**Migration 5: add_package_indexes.py**
```
Revision: mdr_phase1_005
Dependencies: mdr_phase1_004
Operations:
- CREATE INDEX on package_type
- CREATE INDEX on base_package_id
- CREATE INDEX on study_id
```

**Migration 6: migrate_existing_packages.py**
```
Revision: mdr_phase1_006
Dependencies: mdr_phase1_005
Operations:
- UPDATE packages SET package_type = 'tenant' WHERE package_type IS NULL
```

### 9.4 Rollback Plan

Each migration is reversible. Rollback order is reverse of apply order.

```bash
# Rollback all Phase 1 migrations
alembic downgrade mdr_phase1_001-1
```

### 9.5 Testing Migrations

Before merging migration worktree:
1. Apply to fresh database (from backup)
2. Verify all constraints work
3. Test rollback
4. Apply again
5. Run existing tests to confirm no breakage

---

## 10. Testing Strategy

### 10.1 Testing Layers

| Layer | Tool | Scope | Automation |
|-------|------|-------|------------|
| Unit Tests | pytest | Backend functions | CI |
| API Tests | curl scripts | Backend endpoints | CI |
| Component Tests | Jest/Vitest | Frontend components | CI |
| E2E Tests | Browser MCP | Full flows | Agent-driven |
| Integration Tests | Browser MCP + API | Frontend + Backend | Agent-driven |

### 10.2 Browser MCP Testing Strategy

The Browser MCP tool allows agents to:
- Navigate to pages
- Fill forms
- Click buttons
- Verify content
- Take snapshots

**E2E Test Flows for Phase 1**:

**Test 1: View Standard Packages**
```
1. browser_navigate to /packages
2. browser_click on "Standard Packages" tab
3. browser_snapshot to verify standards list displayed
4. Verify STANDARD badge visible
5. Verify "Create from Standard" button visible
```

**Test 2: Create Package from Standard**
```
1. browser_navigate to /packages
2. browser_click "Standard Packages" tab
3. browser_click "Create from Standard" on first package
4. browser_fill package_name with "Test Copy"
5. browser_select package_type as "tenant"
6. browser_click "Create"
7. browser_snapshot to verify redirect to new package
8. Verify inheritance indicator shows source
```

**Test 3: Super Admin Creates Standard**
```
1. Login as super admin
2. browser_navigate to /super-admin/packages
3. browser_click "Create Standard Package"
4. browser_fill package_name with "Standard Safety"
5. browser_click "Create"
6. browser_snapshot to verify package created
7. Verify package visible in standards list
```

### 10.3 Backend Test Scripts

**test_standard_packages.sh** (curl-based):
```bash
# Test STANDARD package visibility
# Test create-from-standard endpoint
# Test deletion protection
# Test RLS policy (standard visible to all)
```

### 10.4 Test Data Requirements

| Entity | Test Data |
|--------|-----------|
| STANDARD Package | "CDISC-Safety-Standard", "CDISC-Efficacy-Standard" |
| TENANT Package | "Tenant-A-Safety", "Tenant-B-Safety" |
| STUDY Package | "STUDY-001-Safety" |
| Super Admin | Use existing super admin account |
| Regular User | Use existing test accounts |

### 10.5 Test Execution Order

1. Backend unit tests (pytest) - immediate feedback
2. Backend API tests (curl) - endpoint validation
3. Frontend component tests - UI logic
4. E2E tests (Browser MCP) - full integration
5. Performance tests - load time validation

### 10.6 Regression Test Suite

**Required regression tests** (must pass before merge):

| Test Script | Description | Must Pass |
|-------------|-------------|-----------|
| `test_packages_crud.sh` | Existing package CRUD operations | Yes |
| `test_crud_simple.sh` | Core study/release/effort CRUD | Yes |
| `test_preflight_comprehensive.sh` | Full pre-flight validation | Yes |
| `test_role_based_permissions.sh` | Role access control | Yes |
| `test_audit_logging.sh` | Audit trail functionality | Yes |

**New test scripts to create**:

| Test Script | Description |
|-------------|-------------|
| `test_standard_packages.sh` | STANDARD package visibility and operations |
| `test_package_inheritance.sh` | Create from standard, inheritance tracking |
| `test_package_rls.sh` | RLS policy validation (cross-tenant) |
| `test_super_admin_packages.sh` | Super admin package management |

---

## 11. Task Breakdown & Dependencies

### 11.1 Complete Task List

#### WT-1: Migrations (Database)

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| M-1 | Create PackageType enum migration | 0.5 | None |
| M-2 | Create column addition migration (incl. created_by_super_admin_id) | 1.5 | M-1 |
| M-3 | Create constraint migration (partial unique indexes) | 1.5 | M-2 |
| M-4 | Create RLS policy migration (read + write policies) | 1 | M-3 |
| M-5 | Create index migration | 0.5 | M-4 |
| M-6 | Modify audit_log to allow NULL tenant_id | 0.5 | M-5 |
| M-7 | Create data migration for existing packages | 0.5 | M-6 |
| M-8 | Test migrations (apply, rollback, apply) | 1 | M-7 |
| M-9 | Document migration procedure | 0.5 | M-8 |

**WT-1 Total**: 7.5 hours

#### WT-2: Backend Models

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| BM-1 | Add PackageType enum to models | 0.5 | M-7 |
| BM-2 | Update Package model with new fields | 1 | BM-1 |
| BM-3 | Add relationships (base_package, study) | 1 | BM-2 |
| BM-4 | Update Package schemas (Pydantic) | 1 | BM-3 |
| BM-5 | Add computed fields to schemas | 1 | BM-4 |
| BM-6 | Run model validator | 0.5 | BM-5 |
| BM-7 | Update __init__.py exports | 0.5 | BM-6 |

**WT-2 Total**: 5.5 hours

#### WT-3: Backend CRUD

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| BC-1 | Update PackageCRUD with type filtering | 1 | BM-7 |
| BC-2 | Add STUDY package access validation in get methods | 1 | BC-1 |
| BC-3 | Add get_standards() method | 1 | BC-2 |
| BC-4 | Add create_from_standard() with deep copy (see 5.7) | 3 | BC-3 |
| BC-5 | Add TextElement resolution for deep copy | 1.5 | BC-4 |
| BC-6 | Add inheritance chain validation | 1 | BC-5 |
| BC-7 | Add get_derived_packages() method | 1 | BC-6 |
| BC-8 | Update delete with dependency check | 1 | BC-7 |
| BC-9 | Add audit logging for new operations (NULL tenant support) | 1 | BC-8 |
| BC-10 | Write CRUD unit tests | 2 | BC-9 |

**WT-3 Total**: 13.5 hours

#### WT-4: Backend API

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| BA-0 | Add ENABLE_STANDARD_PACKAGES feature flag to config.py | 0.5 | BC-10 |
| BA-1 | Add GET /packages/standards endpoint (with feature flag) | 1 | BA-0 |
| BA-2 | Add POST /packages/create-from-standard | 2 | BA-1 |
| BA-3 | Add GET /packages/{id}/derived endpoint | 1 | BA-2 |
| BA-4 | Update GET /packages/ with type filter | 1 | BA-3 |
| BA-5 | Update POST /packages/ with type support | 1 | BA-4 |
| BA-6 | Update DELETE /packages/{id} with checks | 1 | BA-5 |
| BA-7 | Add super admin package CRUD endpoints (with RLS bypass) | 2 | BA-6 |
| BA-8 | Add super admin PackageItem endpoints | 2 | BA-7 |
| BA-9 | Implement WebSocket broadcast_to_all_tenants() method | 1 | BA-8 |
| BA-10 | Add cross-tenant WebSocket broadcasts for STANDARD changes | 1 | BA-9 |
| BA-11 | Write API test script (curl) | 2 | BA-10 |
| BA-12 | Update API documentation | 1 | BA-11 |

**WT-4 Total**: 16.5 hours

#### WT-5: Frontend API Client

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| FA-1 | Add PackageType to TypeScript types | 0.5 | BA-10 |
| FA-2 | Update Package type with new fields | 0.5 | FA-1 |
| FA-3 | Add getStandardPackages() API function | 0.5 | FA-2 |
| FA-4 | Add createFromStandard() API function | 0.5 | FA-3 |
| FA-5 | Add getDerivedPackages() API function | 0.5 | FA-4 |
| FA-6 | Update existing package API functions | 1 | FA-5 |
| FA-7 | Add query hooks for new endpoints | 1 | FA-6 |

**WT-5 Total**: 4.5 hours

#### WT-6: Frontend Components

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| FC-1 | Create PackageTypeBadge component | 1 | FA-7 |
| FC-2 | Create PackageTypeSelector component | 1 | FC-1 |
| FC-3 | Create InheritanceIndicator component | 1 | FC-2 |
| FC-4 | Create CreateFromStandardDialog | 2 | FC-3 |
| FC-5 | Create StandardPackagesList component | 2 | FC-4 |
| FC-6 | Update PackageCard with new UI | 1 | FC-5 |
| FC-7 | Create packageFilterStore (Zustand) | 1 | FC-6 |
| FC-8 | Write component tests | 2 | FC-7 |

**WT-6 Total**: 11 hours

#### WT-7: Frontend Pages

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| FP-1 | Update Packages page with tabs/filters | 2 | FC-8 |
| FP-2 | Update Package detail page with new UI | 2 | FP-1 |
| FP-3 | Create Super Admin Package Management page | 3 | FP-2 |
| FP-4 | Add routes for new pages | 0.5 | FP-3 |
| FP-5 | Update navigation/sidebar | 0.5 | FP-4 |
| FP-6 | Responsive design testing | 1 | FP-5 |

**WT-7 Total**: 9 hours

#### WT-8: Testing & Documentation

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| T-1 | Write E2E test: View Standards (Browser MCP) | 1 | FP-6 |
| T-2 | Write E2E test: Create from Standard (Browser MCP) | 2 | T-1 |
| T-3 | Write E2E test: Super Admin Management (Browser MCP) | 2 | T-2 |
| T-4 | Write E2E test: RLS/Permissions (Browser MCP) | 2 | T-3 |
| T-5 | Write E2E test: Cross-tenant WebSocket (Browser MCP) | 1.5 | T-4 |
| T-6 | Run regression: test_packages_crud.sh | 0.5 | T-5 |
| T-7 | Run regression: test_preflight_comprehensive.sh | 1 | T-6 |
| T-8 | Performance testing (package list < 500ms) | 1 | T-7 |
| T-9 | Update CLAUDE.md with new patterns | 1 | T-8 |
| T-10 | Document test results | 1 | T-9 |

**WT-8 Total**: 14 hours

#### WT-9: Callable Library (Renamed from Macro Library)

**Note**: This worktree can run in parallel with WT-5/6/7 after migrations and models are done.

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| CL-1 | Install pgvector extension, create migration | 1 | M-9 |
| CL-2 | Create Callable, CallableImplementation, CallableParameter models | 2.5 | CL-1, BM-7 |
| CL-3 | Create ParameterLanguageMapping model | 1 | CL-2 |
| CL-4 | Create CallableDocumentation model (with vector) | 1 | CL-3 |
| CL-5 | Create Callable schemas (Pydantic) | 1.5 | CL-4 |
| CL-6 | Create CallableCRUD (basic CRUD) | 2 | CL-5 |
| CL-7 | Create CallableImplementationCRUD | 1.5 | CL-6 |
| CL-8 | Create embedding generation service (OpenAI integration) | 2 | CL-7 |
| CL-9 | Create vector search function (pgvector cosine similarity) | 1.5 | CL-8 |
| CL-10 | Create RAG service (LLM integration for /ask endpoint) | 3 | CL-9 |
| CL-11 | Create callable API endpoints (CRUD) | 2 | CL-10 |
| CL-12 | Create callable implementation endpoints | 1 | CL-11 |
| CL-13 | Create callable search endpoint | 1 | CL-12 |
| CL-14 | Create /callables/ask RAG endpoint | 2 | CL-13 |
| CL-15 | Create super admin callable endpoints | 1 | CL-14 |
| CL-16 | Create callable TypeScript types | 0.5 | CL-15 |
| CL-17 | Create callable API client functions | 1 | CL-16 |
| CL-18 | Create CallableLibraryPage component | 2 | CL-17 |
| CL-19 | Create CallableSearchBar with semantic search | 1.5 | CL-18 |
| CL-20 | Create CallableAskDialog (RAG chat UI) | 2 | CL-19 |
| CL-21 | Create CallableDetailView with language tabs | 2 | CL-20 |
| CL-22 | Create LanguageImplementationEditor | 1.5 | CL-21 |
| CL-23 | Create CallableDocEditor (markdown editor) | 1.5 | CL-22 |
| CL-24 | Write callable library E2E tests (Browser MCP) | 2 | CL-23 |
| CL-25 | Write curl test script for callable API | 1 | CL-24 |

**Study Document Management Tasks** (integrated with Callable Library):

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| SD-1 | Create StudyDocument model with file metadata | 1.5 | CL-1, BM-7 |
| SD-2 | Create StudyDocumentChunk model (with vector) | 1 | SD-1 |
| SD-3 | Create StudyDocument schemas (Pydantic) | 1 | SD-2 |
| SD-4 | Create document parser service (PDF, Word, Excel, TXT) | 3 | SD-3 |
| SD-5 | Create document chunking service (split into ~1000 token chunks) | 2 | SD-4 |
| SD-6 | Create document vectorization service (reuses CL-8) | 1.5 | SD-5, CL-8 |
| SD-7 | Create StudyDocumentCRUD (CRUD + file storage) | 2 | SD-6 |
| SD-8 | Create document search function (pgvector, reuses CL-9) | 1 | SD-7, CL-9 |
| SD-9 | Create document RAG service (reuses CL-10) | 2 | SD-8, CL-10 |
| SD-10 | Create document CRUD endpoints (upload, list, download, delete) | 2 | SD-9 |
| SD-11 | Create vectorization endpoints (start, status, delete vectors) | 1.5 | SD-10 |
| SD-12 | Create study document search endpoint | 1 | SD-11 |
| SD-13 | Create /studies/{id}/documents/ask RAG endpoint | 1.5 | SD-12 |
| SD-14 | Create cross-study search endpoints | 1 | SD-13 |
| SD-15 | Create unified /unified/ask endpoint (callables + documents) | 2 | SD-14, CL-14 |
| SD-16 | Create StudyDocument TypeScript types | 0.5 | SD-15 |
| SD-17 | Create document API client functions | 1 | SD-16 |
| SD-18 | Create StudyDocumentsPanel component | 2 | SD-17 |
| SD-19 | Create DocumentUploadDialog with vectorize option | 2 | SD-18 |
| SD-20 | Create DocumentViewer (preview + metadata) | 1.5 | SD-19 |
| SD-21 | Create DocumentAskDialog (study doc RAG UI) | 2 | SD-20 |
| SD-22 | Create UnifiedSearchDialog (callables + docs) | 2 | SD-21 |
| SD-23 | Add Documents tab to Study detail page | 1 | SD-22 |
| SD-24 | Write study documents E2E tests | 2 | SD-23 |
| SD-25 | Write curl test script for document API | 1 | SD-24 |

**WT-9 Total**: 38 + 38 = 76 hours (Callables + Study Documents)

#### WT-10: Metadata Versioning (NEW)

**Note**: Can run in parallel with WT-9 after migrations and models are done.

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| MV-1 | Create StandardType enum | 0.5 | M-9 |
| MV-2 | Create StandardVersion model with constraints | 2 | MV-1, BM-7 |
| MV-3 | Create MetadataVersionHistory model | 1 | MV-2 |
| MV-4 | Create callable_standard_versions junction table | 1 | MV-3 |
| MV-5 | Add target_standard_version_id to packages | 0.5 | MV-4 |
| MV-6 | Create StandardVersion schemas (Pydantic) | 1 | MV-5 |
| MV-7 | Create StandardVersionCRUD | 2 | MV-6 |
| MV-8 | Create MetadataVersionHistoryCRUD | 1.5 | MV-7 |
| MV-9 | Create tenant standard version API endpoints | 2 | MV-8 |
| MV-10 | Create super admin standard version endpoints | 1.5 | MV-9 |
| MV-11 | Update package API to support standard_version_id | 1 | MV-10 |
| MV-12 | Update callable API to link to standard versions | 1 | MV-11 |
| MV-13 | Create standard version TypeScript types | 0.5 | MV-12 |
| MV-14 | Create standard version API client functions | 1 | MV-13 |
| MV-15 | Create StandardVersionsPage (super admin) | 2 | MV-14 |
| MV-16 | Create StandardVersionSelector component | 1 | MV-15 |
| MV-17 | Create StandardVersionBadge component | 0.5 | MV-16 |
| MV-18 | Create StandardVersionTree (lineage view) | 2 | MV-17 |
| MV-19 | Update Package forms to include version selector | 1 | MV-18 |
| MV-20 | Write versioning E2E tests (Browser MCP) | 2 | MV-19 |
| MV-21 | Write curl test script for versioning API | 1 | MV-20 |

**WT-10 Total**: 26 hours

#### WT-11: CDISC Library Integration (NEW)

**Note**: Depends on WT-10 (Metadata Versioning) for StandardVersion model.

| Task ID | Task | Est. Hours | Dependencies |
|---------|------|------------|--------------|
| CI-1 | Add CDISC config (API key, base URL) to settings | 0.5 | MV-21 |
| CI-2 | Create CDISCDomain, CDISCVariable models | 2 | CI-1 |
| CI-3 | Create CDISCImportLog model | 1 | CI-2 |
| CI-4 | Add CDISC tracking fields to StandardVersion | 1 | CI-3 |
| CI-5 | Create CDISC schemas (Pydantic) | 1.5 | CI-4 |
| CI-6 | Create CDISCLibraryClient service (API wrapper) | 3 | CI-5 |
| CI-7 | Create import service (standard → PEARL mapping) | 4 | CI-6 |
| CI-8 | Create CDISCDomain CRUD | 1.5 | CI-7 |
| CI-9 | Create CDISCVariable CRUD | 1.5 | CI-8 |
| CI-10 | Create browse CDISC products endpoint | 1 | CI-9 |
| CI-11 | Create import preview endpoint | 1.5 | CI-10 |
| CI-12 | Create import standard endpoint | 2 | CI-11 |
| CI-13 | Create import history endpoint | 1 | CI-12 |
| CI-14 | Create domain/variable read endpoints | 1 | CI-13 |
| CI-15 | Create CDISC TypeScript types | 0.5 | CI-14 |
| CI-16 | Create CDISC API client functions | 1 | CI-15 |
| CI-17 | Create CDISCImportPage (super admin) | 2.5 | CI-16 |
| CI-18 | Create CDISCProductBrowser component | 2 | CI-17 |
| CI-19 | Create CDISCImportPreview dialog | 2 | CI-18 |
| CI-20 | Create CDISCDomainViewer page | 2 | CI-19 |
| CI-21 | Write CDISC import E2E tests (Browser MCP) | 2 | CI-20 |
| CI-22 | Write curl test script for CDISC API | 1 | CI-21 |

**WT-11 Total**: 35 hours

### 11.2 Summary

| Worktree | Tasks | Hours |
|----------|-------|-------|
| WT-1: Migrations | 9 | 7.5 |
| WT-2: Models | 7 | 5.5 |
| WT-3: CRUD | 10 | 13.5 |
| WT-4: API | 13 | 16.5 |
| WT-5: FE API | 7 | 4.5 |
| WT-6: FE Components | 8 | 11 |
| WT-7: FE Pages | 6 | 9 |
| WT-8: Testing & Docs | 10 | 14 |
| WT-9: Callable Library + Study Docs | 50 | 76 |
| WT-10: Metadata Versioning | 21 | 26 |
| WT-11: CDISC Import | 22 | 35 |
| **Total** | **163** | **218.5** |

### 11.3 Critical Path

**Standard Packages Path** (Core):
```
M-1 → ... → M-9 (7.5 hrs)
    → BM-1 → ... → BM-7 (5.5 hrs)
        → BC-1 → ... → BC-10 (13.5 hrs)
            → BA-0 → ... → BA-12 (16.5 hrs)
                → FA-1 → ... → FA-7 (4.5 hrs)
                    → FC-1 → ... → FC-8 (11 hrs)
                        → FP-1 → ... → FP-6 (9 hrs)
                            → T-1 → ... → T-10 (14 hrs)
```

**Callable Library Path** (parallel after migrations):
```
CL-1 → CL-2 → ... → CL-25 (38 hrs)
       ↑
       Depends on M-9 and BM-7 only
```

**Metadata Versioning Path** (parallel after migrations):
```
MV-1 → MV-2 → ... → MV-21 (26 hrs)
       ↑
       Depends on M-9 and BM-7 only
```

**CDISC Import Path** (depends on Metadata Versioning):
```
CI-1 → CI-2 → ... → CI-22 (35 hrs)
       ↑
       Depends on MV-21 (Versioning complete)
```

**Critical Path Total**: 81.5 hours (Standard Packages) + 26 hours (Versioning) + 35 hours (CDISC) = 142.5 hours sequential

**With full parallelization** (11 worktrees):
- Core path: 81.5 hours
- Callable Library: 38 hours (parallel with WT-5/6/7/8)
- Metadata Versioning: 26 hours (parallel with WT-5/6/7/8/9)
- CDISC Import: 35 hours (after WT-10 completes)
- Estimated wall-clock time: 50-55 hours with aggressive parallelization
- WT-9/10/11 can overlap partially

---

## 12. Risk Assessment

### 12.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RLS policy breaks existing functionality | Medium | High | Extensive testing before merge, rollback plan |
| Migration conflicts with other development | Medium | Medium | Coordinate with team, use feature flags |
| Performance degradation with new queries | Low | Medium | Add indexes, monitor query plans |
| WebSocket not broadcasting new operations | Low | Low | Follow existing patterns, test manually |

### 12.2 Process Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Worktree merge conflicts | High | Medium | Frequent rebases, clear interface contracts |
| Shared database issues during development | Medium | High | Use separate test databases per worktree |
| Agent coordination failures | Medium | Medium | Clear communication protocol, status file |
| Scope creep | Medium | Medium | Strict adherence to Phase 1 scope |

### 12.3 Mitigation Actions

1. **RLS Testing**: Create comprehensive test script before migration
2. **Database Isolation**: Consider using separate databases for each worktree during development
3. **Feature Flags**: Add `ENABLE_STANDARD_PACKAGES` flag for gradual rollout
4. **Rollback Procedure**: Document and test rollback before go-live

---

## 13. Future Phases Overview

### Phase 1.1: Sync from Standard (Enhancement)

- Detect when standard package has been updated
- "Sync" action to pull changes to derived packages
- Merge conflict resolution UI
- Changelog tracking

### Phase 2: Dataset Specifications

- DatasetDefinition with variable specs
- NCI CT API integration
- Macro automation for datasets
- Dataset program generation

### Phase 3: Full ARS Compliance

- Complete ARS v1.0 data model
- AnalysisSet with compound expressions
- ReportingEvent extensions
- TFL program generation
- ARS JSON-LD export

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| STANDARD Package | Global package managed by super admin, visible to all tenants |
| TENANT Package | Tenant-specific package (current behavior) |
| STUDY Package | Study-specific package, inherits tenant isolation |
| Inheritance | Relationship where one package is derived from another |
| RLS | Row-Level Security - PostgreSQL feature for data isolation |
| Worktree | Git feature allowing multiple branches checked out simultaneously |
| Browser MCP | Model Context Protocol tool for browser automation |

---

## Appendix B: API Reference Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/packages/standards | List standard packages |
| POST | /api/v1/packages/create-from-standard | Create package from standard |
| GET | /api/v1/packages/{id}/derived | List derived packages |
| GET | /api/v1/packages/ | List packages (with type filter) |
| POST | /api/v1/packages/ | Create package (with type) |
| PUT | /api/v1/packages/{id} | Update package |
| DELETE | /api/v1/packages/{id} | Delete package (with checks) |
| POST | /api/v1/super-admin/packages/ | Create standard (super admin) |
| PUT | /api/v1/super-admin/packages/{id} | Update standard (super admin) |
| DELETE | /api/v1/super-admin/packages/{id} | Delete standard (super admin) |

---

## Appendix C: Checklist for Each Worktree Agent

### Before Starting

- [ ] Confirm dependencies are complete (check status file)
- [ ] Pull latest changes from main
- [ ] Ensure database migrations are applied
- [ ] Backend server is running
- [ ] Frontend dev server is running (if applicable)

### During Development

- [ ] Follow PEARL coding patterns (see CLAUDE.md)
- [ ] Add WebSocket broadcasts for CRUD operations
- [ ] Add audit logging for major operations
- [ ] Update status file with progress

### Before Merge

- [ ] All tests pass
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`npm run build` for frontend)
- [ ] Manual testing completed
- [ ] Update status file to "complete"
- [ ] Notify downstream worktrees

---

*End of PRD*
