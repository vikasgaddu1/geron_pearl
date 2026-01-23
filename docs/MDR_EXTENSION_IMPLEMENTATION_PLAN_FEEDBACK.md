# MDR Extension Implementation Plan - Critical Analysis

**Reviewed**: January 2026
**Plan Version**: 1.1
**PRD Reference**: v1.6 (Note: I reviewed PRD v1.5 - new Study Documents feature added)
**Reviewer**: Claude Code

---

## Executive Summary

The implementation plan is well-structured with clear task breakdowns, database isolation strategy, and merge procedures. However, several gaps exist primarily around the new **Study Documents** feature which appears to be a scope addition not present in PRD v1.5.

**Key Finding**: PRD should be updated to v1.6 with Study Documents specification before implementation begins.

---

## 🔴 Critical Gaps

### 1. Study Documents Not in PRD v1.5

**Issue**: The implementation plan references PRD v1.6 and includes Study Documents (38 hours, 25 tasks), but PRD v1.5 does not contain this feature.

**Impact**: High - implementing without PRD specification risks:
- Missing requirements
- Incomplete data model
- No API contracts defined
- No access control rules

**Recommendation**: Update PRD to v1.6 with complete Study Documents specification including:
- Data model (StudyDocument, StudyDocumentChunk)
- API endpoints
- Access control rules (who can upload/delete per study)
- File storage strategy
- Supported formats and size limits

---

### 2. File Storage Strategy Missing

**Location**: SD-7 "Create StudyDocumentCRUD (CRUD + file storage)"

**Issue**: No specification for where uploaded documents are stored:
- Local filesystem?
- S3/MinIO?
- Database BLOB?

**Impact**: High - affects deployment, scaling, backup strategy

**Recommendation**: Add to plan:
```
Storage Options:
- Development: Local filesystem (./uploads/)
- Production: S3-compatible storage (AWS S3, MinIO, Cloudflare R2)

Environment Variables:
STORAGE_BACKEND=local|s3
S3_BUCKET=pearl-documents
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_ENDPOINT_URL=...  # For S3-compatible services
```

---

### 3. RLS Policies for Study Documents Missing

**Issue**: No mention of Row-Level Security for StudyDocument table.

**Impact**: High - security vulnerability if documents accessible across tenants/studies

**Required RLS**:
```sql
-- Read: User must have access to the study
CREATE POLICY study_document_read ON study_documents
FOR SELECT USING (
  tenant_id = current_tenant_id() AND
  study_id IN (SELECT study_id FROM user_study_roles WHERE user_id = current_user_id())
);

-- Write: User must be admin or have LEAD role on the study
CREATE POLICY study_document_write ON study_documents
FOR INSERT, UPDATE, DELETE USING (
  tenant_id = current_tenant_id() AND
  study_id IN (SELECT study_id FROM user_study_roles WHERE user_id = current_user_id() AND role IN ('LEAD', 'ADMIN'))
);
```

---

### 4. Feature Flag for Study Documents Missing

**Issue**: Section 6/10 lists feature flags but no `ENABLE_STUDY_DOCUMENTS`

**Impact**: Medium - cannot independently toggle Study Documents feature

**Recommendation**: Add:
```python
ENABLE_STUDY_DOCUMENTS: bool = Field(default=False)
```

---

### 5. Audit Logging for Study Documents Missing

**Issue**: No mention of audit logging for document operations

**Impact**: Medium - violates PEARL pattern (all major entities need audit logging)

**Required**:
- Log document uploads (CREATE)
- Log document deletions (DELETE)
- Log vectorization toggle (UPDATE)

---

## 🟠 Important Gaps

### 6. WebSocket Events for Study Documents Missing

**Issue**: No WebSocket broadcast events for document operations

**PEARL Pattern**: All CRUD operations broadcast changes

**Required Events**:
| Event | When |
|-------|------|
| `study_document_created` | Document uploaded |
| `study_document_deleted` | Document deleted |
| `study_document_updated` | Vectorization toggled |

---

### 7. Document Validation Rules Missing

**Issue**: No specification for:
- Maximum file size
- Allowed file types validation
- Storage quota per tenant/study

**Recommendation**: Add to SD-4 or SD-7:
```python
# Configuration
MAX_DOCUMENT_SIZE_MB: int = 50  # Per document
MAX_STORAGE_PER_STUDY_MB: int = 500  # Per study
ALLOWED_EXTENSIONS: list = ['.pdf', '.docx', '.xlsx', '.txt', '.md']
```

---

### 8. pgvector Extension Missing for pearl_version_db

**Location**: Section 3 - Database Creation Commands

**Issue**: pgvector only created for `pearl_callable_db` and `pearl_main_db`, not `pearl_version_db`

**Impact**: Low for now, but if CDISC import later needs vector search, this will be a problem

**Recommendation**: Add for consistency:
```bash
psql -U postgres -d pearl_version_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

### 9. Migration Coordination for WT-9 Models

**Issue**: WT-1 only lists migrations for Standard Packages (mdr_001-007). WT-9 models (Callable, CallableImplementation, StudyDocument, StudyDocumentChunk) need their own migrations.

**Current Understanding**: WT-9 uses separate database (`pearl_callable_db`) so creates its own migrations. But this isn't explicitly documented.

**Recommendation**: Add to WT-9 section:
```
**Migrations Created by WT-9**:
- `callable_001_create_pgvector.py`
- `callable_002_create_callable_tables.py`
- `callable_003_create_study_document_tables.py`
```

---

### 10. Study Documents E2E Test Cases Missing

**Location**: WT-8 E2E tests only cover Standard Packages, not Study Documents or Callables

**Issue**: T-1 through T-5 are for Standard Packages. Callable/Study Document E2E tests are in WT-9 (CL-24, SD-24) but not detailed.

**Recommendation**: Add to WT-9 section:
```
E2E Tests for Study Documents:
1. Upload document to study
2. View document list
3. Toggle vectorization
4. Search within study documents
5. Cross-study search (admin only)
6. Delete document
7. Unified search (callables + documents)
```

---

### 11. Unified Search Access Control Not Specified

**Location**: SD-15 "Create unified /unified/ask endpoint"

**Issue**: No specification for:
- Who can use unified search?
- Does it search ALL tenant documents or user-accessible studies only?
- How are callables (global vs tenant) mixed with documents (study-scoped)?

**Recommendation**: Define scope rules:
```
Unified Search Scope:
- Callables: Global + tenant's callables
- Documents: Only from studies user has access to
- Results: Combined, sorted by relevance
- Access: Any authenticated user (scoped by their permissions)
```

---

## 🟡 Minor Gaps

### 12. Architecture Diagram Formatting

**Issue**: ASCII art has misaligned closing brackets

**Impact**: Cosmetic only

---

### 13. Week Timeline vs Hours Discrepancy

**Issue**: "Week 1-2" suggests 2 weeks, but tasks total 13 hours (WT-1 + WT-2). With 8-hour days, this is < 2 days, not 2 weeks.

**Recommendation**: Clarify:
- Is this calendar time (including review, testing, iteration)?
- Or is this assuming part-time work?

---

### 14. Test Script Section Incomplete

**Location**: Section 7 - New Test Scripts

**Issue**: Lists test scripts but doesn't include:
- `test_study_documents.sh`
- `test_document_rag.sh`
- `test_unified_search.sh`

**Recommendation**: Add to list.

---

### 15. Markdown Support Not Listed in Parser Task

**Location**: SD-4 "Create document parser service (PDF, Word, Excel, TXT)"

**Issue**: Completion criteria mentions Markdown but SD-4 doesn't list it.

**Recommendation**: Update SD-4 to include Markdown parsing (trivial - just read as text).

---

## ✅ Strengths

1. **Clear task breakdown** - Each worktree has well-defined tasks with hours and dependencies
2. **Hybrid database strategy** - Good isolation for parallel development
3. **Migration merge strategy** - Alembic multi-head handling documented
4. **Feature flag rollback** - Quick disable without database rollback
5. **Reuse of RAG infrastructure** - SD-6, SD-8, SD-9 reuse callable services
6. **Unified search endpoint** - Good UX for searching across callables + documents
7. **Pre-merge checklist** - Comprehensive quality gates
8. **Dependency list** - Clear Python/npm requirements

---

## Summary: Required Actions Before Implementation

| Priority | Gap | Action |
|----------|-----|--------|
| 🔴 Critical | PRD missing Study Documents | Update PRD to v1.6 with full specification |
| 🔴 Critical | File storage strategy | Define storage backend and configuration |
| 🔴 Critical | Study Documents RLS | Add RLS policy specification |
| 🔴 Critical | Audit logging missing | Add to PEARL patterns |
| 🟠 Important | Feature flag missing | Add `ENABLE_STUDY_DOCUMENTS` |
| 🟠 Important | WebSocket events missing | Define broadcast events |
| 🟠 Important | Document validation rules | Define size/type limits |
| 🟠 Important | WT-9 migration list | Document migrations for callable/document tables |
| 🟠 Important | E2E test cases | Detail Study Documents tests |
| 🟠 Important | Unified search scope | Define access control rules |
| 🟡 Minor | pgvector for version_db | Add for consistency |
| 🟡 Minor | Test scripts list | Add document test scripts |

---

## Recommendation

**Do not start implementation until**:
1. PRD is updated to v1.6 with complete Study Documents specification
2. File storage strategy is defined
3. RLS policies are specified
4. The 4 critical gaps above are addressed

The plan structure is solid - these gaps are specification issues, not architectural problems.

---

*Feedback Document Version: 1.0*
