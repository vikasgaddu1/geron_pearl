# Consolidated Role-Based Access Control Implementation Guide for PEARL

## Executive Summary

This document consolidates the best features from two RBAC implementation approaches, combining comprehensive architectural patterns from the first approach with pragmatic implementation details from the second. The result is a production-ready RBAC system that balances security, usability, and maintainability.

## Core Design Principles

1. **Single Codebase Architecture**: Maintain one admin-frontend application with conditional rendering
2. **Progressive Role Permissions**: Each role inherits permissions from lower levels
3. **Backend-First Security**: All permissions enforced at API level, UI is supplementary
4. **Minimal Initial Complexity**: Start with header-based auth, migrate to JWT/session later
5. **Real-World Focus**: Prioritize practical implementation over theoretical completeness

## Role Definitions and Permissions

### Three-Tier Role System

#### VIEWER Role (Base Level)
**Primary Use Case**: Stakeholders who need visibility into project progress
**Dashboard**: Editor/Viewer Dashboard (simplified, focused on tracking)
**Permissions**:
- ✅ View all Reporting Effort Trackers across all efforts
- ✅ Global search and filtering capabilities
- ✅ Export data (CSV/Excel) for reporting
- ✅ View tracker details, comments, and history
- ✅ Access activity feed and workload summaries
- ❌ Cannot modify any data
- ❌ No access to system configuration

#### EDITOR Role (Operational Level)
**Primary Use Case**: Team members actively working on trackers
**Dashboard**: Editor/Viewer Dashboard (with edit capabilities)
**Inherits**: All VIEWER permissions
**Additional Permissions**:
- ✅ Full tracker form editing:
  - Assign/unassign production and QC programmers
  - Update all status fields (production, QC)
  - Modify priority, due dates, QC levels
  - Add/edit comments and notes
- ✅ Create new tracker items
- ✅ Access workload management features
- ❌ Cannot delete trackers
- ❌ No access to Studies, Database Releases, Reporting Efforts management
- ❌ No bulk operations or import capabilities

#### ADMIN Role (System Level)
**Primary Use Case**: System administrators and project managers
**Dashboard**: Admin Dashboard (full system overview)
**Inherits**: All EDITOR permissions
**Additional Permissions**:
- ✅ Complete system access
- ✅ Full CRUD on all entities (Studies, Database Releases, Reporting Efforts, etc.)
- ✅ Delete trackers and any other entities
- ✅ Bulk operations and data import/export
- ✅ User management and role assignment
- ✅ Database backup and system configuration
- ✅ Audit trail access

## Implementation Architecture

### Backend Implementation (FastAPI)

#### Phase 1: Lightweight Role Enforcement

**Rationale**: Start with header-based authentication for rapid deployment, with clear migration path to robust auth.

**1. Core Security Module**
Location: `backend/app/core/security.py`

```python
# Implementation approach - DO NOT code, provide structure
"""
1. Create UserRole enum with VIEWER, EDITOR, ADMIN values
2. Implement get_current_role() function that:
   - Extracts X-User-Role header from request
   - Validates against UserRole enum
   - Returns normalized role or raises 401 for invalid/missing
   
3. Create require_roles() dependency factory:
   - Takes set of allowed roles as parameter
   - Returns FastAPI Depends function
   - Raises 403 if current role not in allowed set
   - Includes detailed error message for debugging
   
4. Add role_context() dependency for endpoints needing role info:
   - Returns dict with role and derived permissions
   - Caches result per request for efficiency
"""
```

**2. Apply to Tracker Endpoints**
Location: `backend/app/api/v1/reporting_effort_tracker.py`

```python
# Permission mapping - DO NOT code, apply this pattern
"""
Read Operations (VIEWER+):
- GET /reporting-effort-tracker/
- GET /reporting-effort-tracker/{tracker_id}
- GET /reporting-effort-tracker/by-item/{item_id}
- GET /reporting-effort-tracker/export/{reporting_effort_id}

Write Operations (EDITOR+):
- POST /reporting-effort-tracker/
- PUT /reporting-effort-tracker/{tracker_id}
- POST /reporting-effort-tracker/{tracker_id}/assign-programmer
- DELETE /reporting-effort-tracker/{tracker_id}/unassign-programmer
- GET /reporting-effort-tracker/workload-summary
- GET /reporting-effort-tracker/workload/{programmer_id}

Admin Operations (ADMIN only):
- DELETE /reporting-effort-tracker/{tracker_id}
- POST /reporting-effort-tracker/bulk-assign
- POST /reporting-effort-tracker/bulk-status-update
- POST /reporting-effort-tracker/import/{reporting_effort_id}
"""
```

**3. Systematic Application to Other Endpoints**

```python
# Pattern for all modules - DO NOT code, apply systematically
"""
Admin-Only Modules (all endpoints require ADMIN):
- audit_trail.py
- database_backup.py
- users.py
- studies.py (write operations)
- database_releases.py (write operations)
- reporting_efforts.py (write operations)
- packages.py (write operations)
- text_elements.py (write operations)

Mixed Access Modules:
- reporting_effort_items.py: Read (VIEWER+), Write (ADMIN)
- tracker_comments.py: Read (VIEWER+), Write (EDITOR+), Delete (ADMIN)
"""
```

#### Phase 2: Enhanced Security Features

**After initial deployment, implement:**

1. **Audit Logging Enhancement**
   - Log all write operations with user role and ID
   - Track permission denials for security monitoring
   - Include role in WebSocket broadcast metadata

2. **Rate Limiting by Role**
   - VIEWER: Standard rate limits
   - EDITOR: Increased limits for operational work
   - ADMIN: Minimal limits for bulk operations

3. **Field-Level Permissions**
   - Implement @field_permission decorator for granular control
   - Apply to sensitive fields (e.g., financial data)

### Frontend Implementation (R Shiny)

#### Core Role Management

**1. Role Context Setup**
Location: `admin-frontend/modules/utils/auth_utils.R`

```r
# Implementation structure - DO NOT code, provide pattern
"""
create_auth_context():
  1. Check PEARL_DEV_MODE environment variable
  2. If dev mode:
     - Read role from PEARL_DEV_ROLE
     - Read user info from PEARL_DEV_USERNAME, PEARL_DEV_USER_ID
  3. If production:
     - Extract from session$user (RConnect)
     - Map to role via API call or config
  4. Return list with:
     - user_id, username, role
     - is_viewer, is_editor, is_admin (boolean flags)
     - can_edit_tracker, can_delete, can_manage_system
     
with_role_header(request):
  1. Get current role from auth context
  2. Add X-User-Role header to httr2 request
  3. Return modified request
"""
```

**2. API Client Updates**
Location: `admin-frontend/modules/api_client.R`

```r
# Pattern for all API calls - DO NOT code, apply systematically
"""
Every API call should:
1. Start with base request
2. Apply with_role_header()
3. Execute request
4. Handle 403 errors gracefully with user-friendly messages

Example pattern:
request() %>%
  req_url(url) %>%
  with_role_header() %>%
  req_perform()
"""
```

#### Dashboard Implementation

**1. Editor/Viewer Dashboard**
Location: `admin-frontend/modules/editor_viewer_dashboard_ui.R` and `_server.R`

```r
# UI Structure - DO NOT code, implement these components
"""
Dashboard Layout:
1. Header with role indicator and user info
2. KPI Cards Row:
   - Total Active Trackers
   - My Assignments (if EDITOR)
   - Items Pending QC
   - Completed This Week
   - Overdue Items
   
3. Main Content (Tabbed):
   Tab 1: Reporting Efforts Overview
   - Hierarchical table: Study > Database Release > Reporting Effort
   - Progress indicators per effort
   - Click to filter tracker table
   
   Tab 2: Tracker Management
   - Advanced filters panel (collapsible)
   - DT table with conditional actions
   - Real-time WebSocket updates
   
   Tab 3: Workload Analysis (EDITOR+)
   - Programmer workload charts
   - Priority distribution
   - Due date calendar view
   
4. Activity Feed Sidebar:
   - Recent changes (last 24h)
   - Filtered by user's scope
   - Click to navigate to item
"""
```

**2. Conditional UI Rendering**
Location: `admin-frontend/app.R`

```r
# Navigation structure - DO NOT code, implement pattern
"""
Dynamic Navigation based on role:

VIEWER sees:
- Dashboard (Editor/Viewer)
- Trackers (read-only mode)
- Search
- Help

EDITOR sees:
- Dashboard (Editor/Viewer)
- Trackers (full edit mode)
- Workload Management
- Search
- Help

ADMIN sees:
- Dashboard (Admin)
- Full navigation menu
- All management modules
- System configuration
- User management
"""
```

**3. Tracker Module Permissions**
Location: `admin-frontend/modules/reporting_effort_tracker_server.R`

```r
# Conditional rendering - DO NOT code, implement logic
"""
Table Actions Column:
1. Check auth_context()$role
2. For VIEWER:
   - Show only 'View' button
   - Opens read-only modal
3. For EDITOR:
   - Show 'Edit' button
   - Opens full edit modal
   - Hide/disable Delete button
4. For ADMIN:
   - Show all actions
   - Include Delete with confirmation

Edit Modal:
1. For VIEWER:
   - All inputs disabled
   - Hide Save button
   - Show 'Close' only
2. For EDITOR/ADMIN:
   - All inputs enabled
   - Show Save/Cancel
   - Validate on save
"""
```

## Implementation Phases

### Phase 1: Backend Foundation (Week 1)
**Goal**: Establish secure API layer with role enforcement

Day 1-2: Core Security Module
- Implement UserRole enum and role extraction
- Create require_roles dependency
- Add comprehensive error handling

Day 3-4: Tracker Endpoint Protection
- Apply role decorators to all tracker endpoints
- Test each endpoint with different roles
- Document permission matrix

Day 5: System-Wide Application
- Protect admin-only endpoints
- Add role headers to WebSocket broadcasts
- Create curl test scripts for each role

**Deliverables**:
- Working role-based API protection
- Test scripts demonstrating access control
- Updated API documentation with role requirements

### Phase 2: Frontend Role Context (Week 2)
**Goal**: Establish role awareness in Shiny app

Day 1-2: Auth Utils Module
- Create auth context functions
- Implement role header wrapper
- Add development mode support

Day 3-4: API Client Integration
- Update all API calls with role headers
- Add 403 error handling
- Create notification system for permission errors

Day 5: Testing Infrastructure
- Create role switching mechanism for dev
- Test all API calls with each role
- Document role testing procedures

**Deliverables**:
- Role-aware frontend infrastructure
- Seamless API integration with roles
- Development testing capabilities

### Phase 3: Dashboard Development (Week 3)
**Goal**: Create role-appropriate dashboards

Day 1-3: Editor/Viewer Dashboard
- Implement UI layout
- Create KPI calculations
- Add filtering and search
- Integrate real-time updates

Day 4-5: Dashboard Integration
- Wire into app.R
- Test with each role
- Optimize performance

**Deliverables**:
- Functional Editor/Viewer dashboard
- Role-based dashboard switching
- Performance benchmarks

### Phase 4: UI Permission Enforcement (Week 4)
**Goal**: Complete frontend permission implementation

Day 1-2: Navigation Control
- Implement conditional nav rendering
- Hide/show modules by role
- Add role indicators

Day 3-4: Tracker Module Updates
- Add conditional action buttons
- Implement read-only mode
- Test edit permissions

Day 5: End-to-End Testing
- Test complete workflows per role
- Verify permission boundaries
- Document user journeys

**Deliverables**:
- Fully role-aware UI
- Complete permission enforcement
- User journey documentation

### Phase 5: Production Readiness (Week 5)
**Goal**: Prepare for deployment

Day 1-2: Security Hardening
- Security audit of all endpoints
- Penetration testing simulation
- Fix any vulnerabilities

Day 3-4: Performance Optimization
- Load testing with multiple concurrent users
- Optimize slow queries
- Implement caching where appropriate

Day 5: Documentation and Training
- Create role-specific user guides
- Record training videos
- Prepare deployment runbook

**Deliverables**:
- Security audit report
- Performance benchmarks
- Complete documentation suite

## Testing Strategy

### Backend Testing

**1. Unit Tests**
```python
# Test structure - DO NOT code, implement pattern
"""
test_role_extraction.py:
- Test valid role headers
- Test invalid/missing headers
- Test role normalization

test_role_permissions.py:
- Test each endpoint with each role
- Verify correct status codes (200, 403, 401)
- Test permission inheritance
"""
```

**2. Integration Tests**
```bash
# Create test scripts - DO NOT code, implement pattern
"""
test_viewer_access.sh:
- Test all GET endpoints (expect 200)
- Test POST/PUT/DELETE (expect 403)
- Verify response content

test_editor_access.sh:
- Test tracker CRUD (except DELETE)
- Test assignment operations
- Verify workload access

test_admin_access.sh:
- Test full CRUD on all entities
- Test bulk operations
- Verify system management
"""
```

### Frontend Testing

**1. Manual Test Scenarios**
```
VIEWER Checklist:
□ Can see Editor/Viewer dashboard
□ Can search all trackers
□ Cannot see edit/delete buttons
□ Can export data to CSV/Excel
□ Cannot access admin modules

EDITOR Checklist:
□ Can edit tracker forms
□ Can assign/unassign programmers
□ Cannot delete trackers
□ Cannot access Studies management
□ Can see workload analysis

ADMIN Checklist:
□ Can see Admin dashboard
□ Has full navigation menu
□ Can delete any entity
□ Can perform bulk operations
□ Can manage users
```

**2. Automated Testing (Playwright)**
```javascript
// Test structure - DO NOT code, implement pattern
"""
role-viewer.spec.ts:
- Navigate to dashboard
- Verify read-only UI
- Test search functionality
- Verify export works

role-editor.spec.ts:
- Test tracker editing
- Verify delete is blocked
- Test assignment features
- Check workload access

role-admin.spec.ts:
- Test full CRUD operations
- Verify bulk operations
- Test user management
- Check system configuration
"""
```

## Security Considerations

### Defense in Depth
1. **API Level**: Primary enforcement via require_roles
2. **UI Level**: Hide/disable based on role (UX only)
3. **Database Level**: Consider row-level security in future
4. **Network Level**: Use HTTPS, implement rate limiting

### Security Best Practices
1. **Never trust client**: Always validate on backend
2. **Fail secure**: Default to denying access
3. **Audit everything**: Log all permission checks
4. **Minimize exposure**: Only show what user needs
5. **Regular reviews**: Audit role assignments quarterly

### Migration Path to Production Auth
1. **Current**: Header-based (X-User-Role)
2. **Next**: JWT tokens with role claims
3. **Future**: Integration with enterprise SSO
4. **Consider**: OAuth2/OIDC for external users

## Configuration Management

### Development Environment
```bash
# .env.development
PEARL_DEV_MODE=true
PEARL_DEV_USER_ID=1
PEARL_DEV_USERNAME=test_user
PEARL_DEV_ROLE=EDITOR  # Change for testing
PEARL_DEV_DEPARTMENT=PROGRAMMING

# Backend
PEARL_API_URL=http://localhost:8000
PEARL_WS_URL=ws://localhost:8000/ws
```

### Production Environment
```bash
# .env.production
PEARL_DEV_MODE=false
PEARL_AUTH_PROVIDER=rconnect  # or jwt, oauth2
PEARL_SESSION_TIMEOUT=3600
PEARL_ROLE_CACHE_TTL=300

# API Configuration
PEARL_API_URL=https://api.pearl.example.com
PEARL_WS_URL=wss://api.pearl.example.com/ws
```

### Role Assignment Configuration
```yaml
# config/role_mappings.yaml
role_mappings:
  default_role: VIEWER
  
  group_mappings:
    programming_team: EDITOR
    project_managers: ADMIN
    stakeholders: VIEWER
  
  user_overrides:
    john.doe: ADMIN
    jane.smith: EDITOR
```

## Performance Optimizations

### Backend Optimizations
1. **Cache role checks**: Store in request context
2. **Bulk permission checks**: Validate once for batch operations
3. **Indexed queries**: Add indexes for user_id, role columns
4. **Connection pooling**: Optimize for concurrent users

### Frontend Optimizations
1. **Lazy loading**: Load admin modules only for admins
2. **Memoization**: Cache permission calculations
3. **Debounced updates**: Batch WebSocket updates
4. **Virtual scrolling**: For large tracker tables

### Caching Strategy
1. **Role cache**: 5-minute TTL
2. **Permission cache**: Per session
3. **Dashboard metrics**: 1-minute TTL
4. **Static resources**: 1-hour TTL

## Monitoring and Metrics

### Key Metrics to Track
1. **Security Metrics**:
   - Failed authentication attempts
   - Permission denial rate by role
   - Suspicious activity patterns

2. **Usage Metrics**:
   - Active users by role
   - Feature usage by role
   - API calls by endpoint and role

3. **Performance Metrics**:
   - Dashboard load time by role
   - API response time by role
   - WebSocket message latency

### Alerting Thresholds
- \>10 permission denials/minute from same user
- \>5 failed auth attempts from same IP
- Dashboard load time >3 seconds
- API response time >500ms for read operations

## Rollback Strategy

### Phased Rollout Plan
1. **Phase 1**: Deploy to staging, test with team
2. **Phase 2**: Beta group (5-10 users)
3. **Phase 3**: Department rollout (by role)
4. **Phase 4**: Organization-wide deployment

### Rollback Procedures
1. **Feature flags**: Toggle role enforcement on/off
2. **Database backup**: Before any role migration
3. **Quick disable**: Environment variable to bypass roles
4. **Fallback UI**: Keep existing UI available

### Emergency Procedures
```bash
# Disable role enforcement (backend)
export PEARL_RBAC_ENABLED=false
systemctl restart pearl-api

# Switch all users to ADMIN (emergency)
export PEARL_EMERGENCY_ADMIN_MODE=true
systemctl restart pearl-api
```

## Success Criteria

### Technical Success Metrics
- Zero unauthorized access incidents
- <2% permission denial rate for legitimate requests
- <3 second dashboard load time
- >99.9% API availability

### Business Success Metrics
- 90% user satisfaction by role
- 50% reduction in permission-related support tickets
- 100% compliance with security audit
- 30% improvement in task completion time

### User Adoption Metrics
- 95% of users using appropriate dashboard
- <5% of users requesting role changes
- 80% feature utilization by role
- Positive feedback in user surveys

## Future Enhancements

### Short-term (3-6 months)
1. JWT-based authentication
2. Role hierarchy refinement
3. Custom role creation
4. Temporary permission elevation

### Medium-term (6-12 months)
1. Field-level permissions
2. Data-level security (row-level)
3. Advanced audit trails
4. Role-based notifications

### Long-term (12+ months)
1. ML-based anomaly detection
2. Automated role recommendations
3. Zero-trust architecture
4. Federated authentication

## Appendix: Decision Rationale

### Why Header-Based Auth Initially?
- **Pros**: Quick implementation, easy testing, clear migration path
- **Cons**: Less secure than tokens, requires discipline
- **Mitigation**: HTTPS required, short-term solution only

### Why Three Roles Instead of More?
- **Pros**: Simple to understand, covers 95% of use cases, easier to maintain
- **Cons**: Less granular, may need custom permissions later
- **Future**: Can add sub-roles or permissions without breaking existing

### Why Single Codebase?
- **Pros**: Easier maintenance, consistent experience, simpler deployment
- **Cons**: Larger bundle size, potential security exposure
- **Mitigation**: Lazy loading, code splitting, careful permission checks

### Why Editor/Viewer Share Dashboard?
- **Pros**: Similar needs, reduces duplication, easier training
- **Cons**: Slightly different optimal layouts
- **Future**: Can specialize with tabs or preferences

## Implementation Checklist

### Pre-Implementation
- [ ] Review and approve this plan
- [ ] Set up development environments
- [ ] Create test user accounts
- [ ] Prepare rollback procedures

### Backend Implementation
- [ ] Implement UserRole enum
- [ ] Create require_roles dependency
- [ ] Apply to tracker endpoints
- [ ] Apply to admin endpoints
- [ ] Add role to WebSocket
- [ ] Create test scripts
- [ ] Document API changes

### Frontend Implementation
- [ ] Create auth_utils module
- [ ] Update API client
- [ ] Build Editor/Viewer dashboard
- [ ] Implement conditional navigation
- [ ] Update tracker module
- [ ] Add role indicators
- [ ] Test all roles

### Testing & Validation
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing complete
- [ ] Playwright tests passing
- [ ] Security audit complete
- [ ] Performance benchmarks met
- [ ] Documentation complete

### Deployment
- [ ] Staging deployment
- [ ] Beta user testing
- [ ] Training completed
- [ ] Production deployment
- [ ] Monitoring active
- [ ] Success metrics tracked

## Contact and Support

For questions or issues during implementation:
- Technical Lead: [Specify contact]
- Security Team: [Specify contact]
- DevOps Team: [Specify contact]
- Product Owner: [Specify contact]

## Document Version

- Version: 1.0
- Date: 2025-08-22
- Status: FINAL - Ready for Implementation
- Next Review: After Phase 1 completion