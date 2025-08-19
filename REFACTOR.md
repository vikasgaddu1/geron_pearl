## WebSocket Implementation Refactoring & Code Standardization Request

**Objective**: Analyze the current PEARL application codebase to identify and fix inconsistencies, reduce redundancy, and establish a unified approach for WebSocket implementation and naming conventions.

### Current State Analysis (COMPLETED)

#### 1. WebSocket Implementation Issues Found
- **THREE approaches exist** (not two as originally thought):
  1. **Universal CRUD Manager** (crud_activity_manager.js) - Most sophisticated, context-aware
  2. **Global Observer Pattern** (app.R observers) - Legacy approach for cross-browser sync
  3. **Direct Module Notification** (notifyShinyModule) - Simple but inconsistent
- **Inconsistent routing logic** - Some entities use multiple approaches simultaneously causing race conditions
- **Missing cross-browser sync** for some entities (e.g., study events lack global routing)

#### 2. Naming Convention Inconsistencies Identified

**Backend (Python/FastAPI):**
- Mixed patterns: `CRUDUser` vs `StudyCRUD` vs `PackageCRUD` class naming
- WebSocket events: `reporting_effort_tracker_*` (verbose) vs `package_*` (concise)
- Database tables: Correct snake_case but inconsistent pluralization
- API endpoints: Generally consistent `/api/v1/{entity}` pattern

**Frontend (R/Shiny):**
- Module naming: `packages_simple` (temporary debug name still in use) vs `package_items`
- Function names: Mix of `load_data()`, `loadData()`, `get_data()` patterns
- Reactive values: Inconsistent - some use `{entity}_data`, others just `data`
- Input IDs: Mix of patterns, no consistent namespacing

**Cross-Component:**
- Entity naming mismatches: backend `reporting_effort` vs frontend `reportingEffort` in some places
- WebSocket message type routing depends on string prefix matching (fragile)

#### 3. Code Duplication Found

**Backend Duplication:**
- **Deletion protection logic** repeated in 3+ endpoints (studies, database_releases, packages)
- **WebSocket broadcast functions** nearly identical across 12 files
- **Pydantic model validation** error handling duplicated
- **CRUD base operations** (get, create, update, delete) reimplemented in each CRUD class

**Frontend Duplication:**
- **Form validation setup** duplicated in every R module (10+ copies)
- **API error handling** copy-pasted across all modules
- **DataTable configuration** repeated with slight variations
- **Modal dialog creation** patterns duplicated

### Phase 0: Developer Documentation Generation (NEW - PREREQUISITE)

Before any refactoring begins, we need comprehensive documentation of the existing system to prevent reinventing the wheel.

#### Documentation Structure to Generate:
```markdown
docs/
├── API_REFERENCE.md          # All endpoints with parameters, request/response formats
├── WEBSOCKET_EVENTS.md        # All WebSocket message types and their handlers
├── CRUD_METHODS.md           # All CRUD operations available in each class
├── FRONTEND_MODULES.md       # All R Shiny modules, their functions and patterns
├── DATABASE_SCHEMA.md        # Current schema with relationships and constraints
├── UTILITY_FUNCTIONS.md      # Reusable utilities that already exist
├── NAMING_CONVENTIONS.md     # Agreed upon naming standards
└── CODE_PATTERNS.md          # Common patterns to reuse (validation, error handling, etc.)
```

#### Auto-Documentation Tasks:
1. **Extract all API endpoints** from FastAPI router with parameters
2. **Catalog all WebSocket events** with source and destination mappings
3. **Document existing utilities** to avoid recreation
4. **Map module dependencies** to understand impact of changes
5. **Create pattern library** from existing working code

### Parallel Agent-Based Refactoring Strategy (NEW)

#### Agent 1: Frontend Refactoring Specialist
**Focus**: admin-frontend directory only

**Agent Task Description**:
```markdown
CONTEXT: PEARL R Shiny frontend with THREE WebSocket approaches causing conflicts.

CRITICAL FIRST TASK:
- Rename packages_simple → packages everywhere (this was debug code)

MAIN TASKS:
1. Consolidate to Universal CRUD Manager approach only
2. Remove duplicate global observers in app.R
3. Create reusable module base: modules/utils/crud_base.R
4. Standardize all function names to snake_case
5. Fix module IDs to match pattern: {entity}

CONSTRAINTS:
- Do NOT change API endpoint paths
- Test after EVERY module change
- Maintain WebSocket message compatibility
```

#### Agent 2: Backend Refactoring Specialist  
**Focus**: backend directory only

**Agent Task Description**:
```markdown
CONTEXT: PEARL FastAPI backend with duplicate CRUD operations and broadcast functions.

MAIN TASKS:
1. Create app/crud/base.py with BaseCRUD class
2. Implement app/api/v1/utils/websocket_utils.py for broadcasting
3. Standardize to {Entity}CRUD naming pattern
4. Extract deletion protection to utils/deletion.py
5. Ensure WebSocket events follow {entity}_{action} pattern

CONSTRAINTS:
- Do NOT change database schema
- Keep API response formats identical
- Run ./test_crud_simple.sh after each change
```

### Coordination Points Between Agents:
1. **WebSocket message format** - Must agree before changes
2. **Entity naming** - Must be consistent across stack
3. **API contracts** - Frontend must match backend
4. **Testing integration** - Both test together at checkpoints

### Deliverables Required:

#### 1. Refactoring Plan Document (THIS DOCUMENT)

#### 2. Naming Convention Standard (UPDATED)
```markdown
## PEARL Naming Convention Standard

### Database Layer:
- Tables: `snake_case` plural (e.g., `reporting_efforts`, `packages`)
- Columns: `snake_case` (e.g., `created_at`, `study_id`)
- Foreign keys: `{entity}_id` pattern (e.g., `package_id`)
- Indexes: `idx_{table}_{column(s)}` pattern

### Python/FastAPI:
- CRUD Classes: `{Entity}CRUD` pattern (e.g., `StudyCRUD`, `PackageCRUD`, NOT `CRUDUser`)
- Model Classes: `PascalCase` matching table (e.g., `ReportingEffort`)
- Schema Classes: `{Entity}{Action}` (e.g., `PackageCreate`, `StudyUpdate`)
- Functions: `snake_case` (e.g., `get_reporting_effort`)
- Constants: `UPPER_SNAKE_CASE`
- WebSocket events: `{entity}_{action}` (e.g., `package_created`, `study_updated`)
- API endpoints: `/api/v1/{entities}` plural

### R/Shiny:
- Module files: `{entity}_ui.R` and `{entity}_server.R` (NO MORE packages_simple!)
- Module IDs: `{entity}` (e.g., moduleServer(id = "packages"))
- Functions: `snake_case` ONLY (e.g., `load_packages_data`, NOT `loadPackagesData`)
- Reactive values: `{entity}_data` pattern
- Input IDs: `{action}_{type}` (e.g., `create_btn`, `edit_modal`)

### JavaScript:
- Classes: `PascalCase` (e.g., `UniversalCRUDManager`)
- Methods: `camelCase` (e.g., `handleWebSocketMessage`)
- Constants: `UPPER_SNAKE_CASE`
- WebSocket routing: Use mapping object, not string prefix matching
```

#### 3. Refactoring Implementation Timeline

**Parallel Execution with Two Agents:**

```markdown
## Week 1: Documentation & Setup (Both Agents)

Day 1-2: Generate Documentation
- Agent 1 & 2 Together: Auto-generate all documentation
- Create API_REFERENCE.md, WEBSOCKET_EVENTS.md, etc.
- Document all existing utility functions to avoid recreation

Day 3-4: Test Suite Creation
- Create Playwright automated tests for current functionality
- Document current behavior with screenshots
- Set up feature flags for gradual migration

Day 5: Critical Rename
- BOTH AGENTS: Coordinate packages_simple → packages rename
- Frontend: Rename files and module IDs
- Backend: Ensure endpoints remain compatible

## Week 2: Core Refactoring (Parallel Work)

FRONTEND AGENT (Days 6-10):
1. Create modules/utils/crud_base.R
2. Consolidate to Universal CRUD Manager only
3. Remove duplicate global observers
4. Standardize all functions to snake_case
5. Fix reactive value patterns

BACKEND AGENT (Days 6-10):
1. Create app/crud/base.py with BaseCRUD
2. Create app/api/v1/utils/websocket_utils.py
3. Standardize CRUD class naming
4. Extract deletion protection logic
5. Unify WebSocket event naming

Daily Sync Points:
- Morning: Agree on any API/WebSocket changes
- Evening: Integration testing together

## Week 3: Integration & Cleanup

Day 11-12: Integration Testing
- Both agents test cross-stack functionality
- Fix any contract mismatches
- Performance testing

Day 13-14: Documentation & Cleanup
- Update CLAUDE.md with new patterns
- Remove deprecated code
- Final testing

Day 15: Production Readiness
- Merge to main branch
- Deploy with feature flags
- Monitor for issues
```

#### 4. Code Reduction Opportunities (EXPANDED)

```markdown
## Consolidation Targets

### Backend Patterns to Functionalize:
1. Deletion protection checks (repeated in 5+ endpoints)
   - Create: `check_deletion_dependencies()` utility
   - Location: New file `app/api/v1/utils/deletion.py`
   - Estimated reduction: 200+ lines

2. WebSocket broadcast patterns (12 duplicate functions)
   - Create: Generic `broadcast_entity_change()` function
   - Location: `app/api/v1/utils/websocket_utils.py`
   - Estimated reduction: 300+ lines

3. Base CRUD operations
   - Create: `BaseCRUD` class with common methods
   - Location: `app/crud/base.py`
   - Estimated reduction: 500+ lines

4. Pydantic validation error handling
   - Create: `handle_validation_error()` decorator
   - Location: `app/api/v1/utils/validation.py`
   - Estimated reduction: 150+ lines

### Frontend Patterns to Modularize:
1. Form validation setup (repeated in 10+ modules)
   - Create: `setup_form_validation()` utility
   - Location: `admin-frontend/modules/utils/validation.R`
   - Estimated reduction: 400+ lines

2. API error handling (duplicated everywhere)
   - Create: `handle_api_response()` wrapper
   - Location: `admin-frontend/modules/utils/api_utils.R`
   - Estimated reduction: 300+ lines

3. DataTable configuration
   - Create: `create_standard_datatable()` function
   - Location: `admin-frontend/modules/utils/datatable_utils.R`
   - Estimated reduction: 250+ lines

4. Modal dialog patterns
   - Create: `create_crud_modal()` generator
   - Location: `admin-frontend/modules/utils/modal_utils.R`
   - Estimated reduction: 350+ lines

### JavaScript Consolidation:
1. WebSocket routing logic
   - Create: `WebSocketRouter` class
   - Replace: 200+ lines of if/else chains
   - Location: `admin-frontend/www/websocket_router.js`

2. CRUD activity handling
   - Enhance: Existing `UniversalCRUDManager`
   - Remove: All other approaches
   - Estimated reduction: 500+ lines

TOTAL ESTIMATED CODE REDUCTION: ~3,000 lines (30-40% of duplicated code)
```

### Execution Instructions (ENHANCED):

#### Pre-Flight Checklist:
- [ ] Both agents have read CLAUDE.md and understand constraints
- [ ] Test environment set up and working
- [ ] Backup of current working state created
- [ ] Feature flags configured for gradual rollout

#### Execution Rules:
1. **Incremental Approach**: One module/entity at a time, never "big bang"
2. **Continuous Testing**: Both servers running, test after EVERY change
3. **Atomic Commits**: One logical change per commit with clear message
4. **Real-time Documentation**: Update docs AS you refactor, not after
5. **Instant Rollback**: At first sign of breaking change, revert immediately

#### Agent Coordination Protocol:
```markdown
Daily Standup (5 min):
- Frontend Agent: Current module, blockers
- Backend Agent: Current entity, blockers
- Agree on any API/WebSocket format changes

Checkpoint (Every 2 hours):
- Run integration tests
- Verify no regressions
- Commit if stable

End of Day:
- Full system test
- Document progress
- Plan next day
```

### Success Criteria (MEASURABLE):

- [ ] WebSocket approaches reduced from 3 to 1 (Universal CRUD Manager only)
- [ ] CRUD class naming 100% consistent ({Entity}CRUD pattern)
- [ ] packages_simple renamed to packages everywhere
- [ ] Code duplication reduced by 3,000+ lines (30-40%)
- [ ] All 12 WebSocket broadcast functions consolidated to 1
- [ ] Form validation utility created and used in all 10+ modules
- [ ] Zero production bugs introduced (monitored for 1 week post-deployment)
- [ ] Page load time maintained or improved (<2 seconds)
- [ ] WebSocket message processing <50ms
- [ ] All existing tests still pass

### What NOT to Change (CRITICAL):

- **Database schema structure** (only rename columns if absolutely necessary)
- **API endpoint URLs** (must remain backward compatible)
- **WebSocket message data structure** (only standardize event names)
- **Business logic** (this is refactoring, not feature development)
- **Third-party integrations** (maintain all external contracts)
- **Authentication/Authorization** (security-critical, don't touch)

### Rollback Strategy:

```bash
# If anything breaks:
1. Immediate: git stash  # Save current work
2. Test: Does it work now?
3. If no: git checkout .  # Revert all changes
4. If yes: Investigate stashed changes
5. Nuclear option: git reset --hard origin/main

# Feature flag rollback:
Set ENABLE_REFACTORED_WEBSOCKET=false in .env
```

### Post-Refactoring Validation:

Week 1 after deployment:
- Monitor error logs daily
- Track WebSocket disconnection rates
- Measure page load times
- Survey users for any issues

### Documentation Deliverables:

1. **REFACTORING_LOG.md** - Daily progress and decisions
2. **API_MIGRATION.md** - Any API changes made
3. **PATTERNS.md** - New reusable patterns created
4. **LESSONS_LEARNED.md** - What worked, what didn't

