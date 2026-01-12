# PEARL Manual Testing Guide

This comprehensive testing guide is designed for human testers to verify all CRUD operations, business rules, role-based access, and real-time functionality of the PEARL application.

---

## Table of Contents

1. [Test Environment Setup](#1-test-environment-setup)
2. [Test Data Reference](#2-test-data-reference)
3. [Phase 1: User Management & Authentication](#phase-1-user-management--authentication)
4. [Phase 2: Core Hierarchy CRUD](#phase-2-core-hierarchy-crud)
5. [Phase 3: TFL Properties Management](#phase-3-tfl-properties-management)
6. [Phase 4: Package Management](#phase-4-package-management)
7. [Phase 5: Tracker Workflow](#phase-5-tracker-workflow)
8. [Phase 6: Comments & Notifications](#phase-6-comments--notifications)
9. [Phase 7: Role-Based Access Control](#phase-7-role-based-access-control)
10. [Phase 8: Real-Time Updates (WebSocket)](#phase-8-real-time-updates-websocket)
11. [Phase 9: Business Rule Validation](#phase-9-business-rule-validation)
12. [Phase 10: Audit Trail Verification](#phase-10-audit-trail-verification)
13. [Test Results Summary](#test-results-summary)

---

## 1. Test Environment Setup

### Prerequisites
- [ ] Backend server running at `http://localhost:8000`
- [ ] Frontend running at `http://localhost:5173`
- [ ] Fresh database (or clear test data from previous runs)
- [ ] Two browser windows/tabs ready (for WebSocket testing)

### Initial Login
1. Navigate to `http://localhost:5173`
2. Login with default admin credentials:
   - **Username:** `admin`
   - **Password:** `admin123`

---

## 2. Test Data Reference

Use these exact values during testing for consistency. Copy-paste recommended.

### Users to Create

| Username | Email | Password | Admin | Department | Role Assignment |
|----------|-------|----------|-------|------------|-----------------|
| `test_lead` | `lead@test.com` | `LeadPass123!` | No | `Biostatistics` | LEAD on TEST-001 |
| `test_editor` | `editor@test.com` | `EditorPass123!` | No | `Programming` | EDITOR on TEST-001 |
| `test_viewer` | `viewer@test.com` | `ViewerPass123!` | No | `Clinical` | VIEWER on TEST-001 |
| `test_prog1` | `prog1@test.com` | `Prog1Pass123!` | No | `Programming` | EDITOR on TEST-001 |
| `test_prog2` | `prog2@test.com` | `Prog2Pass123!` | No | `Programming` | EDITOR on TEST-001 |

### Study Hierarchy

| Study | Database Release | Release Date |
|-------|-----------------|--------------|
| `TEST-001` | `DBR-001` | `2026-01-15` |
| `TEST-001` | `DBR-002` | `2026-02-15` |
| `TEST-002` | `DBR-001` | `2026-03-01` |

### TFL Properties (Text Elements)

| Type | Label | Content |
|------|-------|---------|
| `title` | `Safety Summary` | `Summary of Treatment-Emergent Adverse Events` |
| `title` | `Efficacy Summary` | `Summary of Primary Efficacy Endpoints` |
| `footnote` | `AE Source` | `Source: Adverse Events dataset (ADAE)` |
| `footnote` | `Inclusion` | `Includes all randomized subjects` |
| `population_set` | `SAFFL` | `Safety Population` |
| `population_set` | `ITTFL` | `Intent-to-Treat Population` |
| `acronyms_set` | `AE` | `Adverse Event` |
| `acronyms_set` | `SAE` | `Serious Adverse Event` |
| `ich_category` | `ICH_11.4` | `Extent of Exposure` |

### Package Data

| Package Name | Indication | Therapeutic Area |
|--------------|------------|------------------|
| `PKG-SAFETY-001` | `Type 2 Diabetes` | `Metabolic` |
| `PKG-EFFICACY-001` | `Type 2 Diabetes` | `Metabolic` |

### Package Items (TLF)

| Code | Description | Type | Subtype |
|------|-------------|------|---------|
| `T-14.1.1` | `Summary of AEs` | TLF | Table |
| `T-14.2.1` | `AEs by System Organ Class` | TLF | Table |
| `L-16.1.1` | `Subject Listing` | TLF | Listing |
| `F-14.1.1` | `Forest Plot of AEs` | TLF | Figure |

### Package Items (Dataset)

| Code | Description | Type | Subtype |
|------|-------------|------|---------|
| `ADAE` | `Analysis Dataset for AEs` | Dataset | ADaM |
| `ADSL` | `Subject Level Analysis Dataset` | Dataset | ADaM |

---

## Phase 1: User Management & Authentication

### 1.1 Create Test Users (Admin Only)

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 1.1.1 | Create LEAD user | 1. Navigate to User Management<br>2. Click "Add User"<br>3. Enter: `test_lead`, `lead@test.com`, `LeadPass123!`, Admin: No, Dept: Biostatistics<br>4. Save | User created, appears in list | ☐ |
| 1.1.2 | Create EDITOR user | Create user with: `test_editor`, `editor@test.com`, `EditorPass123!` | User created | ☐ |
| 1.1.3 | Create VIEWER user | Create user with: `test_viewer`, `viewer@test.com`, `ViewerPass123!` | User created | ☐ |
| 1.1.4 | Create programmer 1 | Create user with: `test_prog1`, `prog1@test.com`, `Prog1Pass123!` | User created | ☐ |
| 1.1.5 | Create programmer 2 | Create user with: `test_prog2`, `prog2@test.com`, `Prog2Pass123!` | User created | ☐ |

### 1.2 Duplicate User Validation

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 1.2.1 | Duplicate username | Try to create user with username `test_lead` | Error: Username already exists | ☐ |
| 1.2.2 | Duplicate email | Try to create user with email `lead@test.com` | Error: Email already exists | ☐ |

### 1.3 User Update

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 1.3.1 | Update user department | Edit `test_lead`, change department to `Statistics` | Department updated | ☐ |
| 1.3.2 | Update user email | Edit `test_editor`, change email to `editor_new@test.com` | Email updated | ☐ |

### 1.4 Authentication Tests

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 1.4.1 | Valid login | Logout, login as `test_lead` with `LeadPass123!` | Successful login | ☐ |
| 1.4.2 | Invalid password | Try login with wrong password `wrongpass` | Error: Invalid credentials | ☐ |
| 1.4.3 | Invalid username | Try login with `nonexistent` user | Error: Invalid credentials | ☐ |
| 1.4.4 | Logout | Click logout button | Redirected to login page | ☐ |

---

## Phase 2: Core Hierarchy CRUD

### 2.1 Study Management

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.1.1 | Create Study 1 | 1. Navigate to Study Management<br>2. Click "Add Study"<br>3. Enter `TEST-001`<br>4. Save | Study created, appears in list | ☐ |
| 2.1.2 | Create Study 2 | Create study `TEST-002` | Study created | ☐ |
| 2.1.3 | Duplicate study | Try to create study `TEST-001` again | Error: Study already exists | ☐ |
| 2.1.4 | Update study | Edit `TEST-002`, rename to `TEST-002-UPDATED` | Study renamed | ☐ |
| 2.1.5 | Rename back | Edit back to `TEST-002` | Study renamed | ☐ |

### 2.2 Study Member Assignment

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.2.1 | Open members dialog | Click "Members" on `TEST-001` | Members dialog opens | ☐ |
| 2.2.2 | Assign LEAD | Assign `test_lead` as LEAD | User appears with LEAD role | ☐ |
| 2.2.3 | Assign EDITOR | Assign `test_editor` as EDITOR | User appears with EDITOR role | ☐ |
| 2.2.4 | Assign VIEWER | Assign `test_viewer` as VIEWER | User appears with VIEWER role | ☐ |
| 2.2.5 | Assign programmers | Assign `test_prog1` and `test_prog2` as EDITOR | Both appear as EDITOR | ☐ |

### 2.3 Database Release Management

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.3.1 | Create DB Release 1 | 1. Click on `TEST-001`<br>2. Add Database Release<br>3. Enter `DBR-001`, Date: `2026-01-15`<br>4. Save | Release created | ☐ |
| 2.3.2 | Create DB Release 2 | Add `DBR-002` with date `2026-02-15` | Release created | ☐ |
| 2.3.3 | Duplicate release | Try to create `DBR-001` again for `TEST-001` | Error: Release already exists | ☐ |
| 2.3.4 | Create release for Study 2 | Navigate to `TEST-002`, add `DBR-001` with date `2026-03-01` | Release created | ☐ |
| 2.3.5 | Update release date | Edit `DBR-001` on `TEST-001`, change date to `2026-01-20` | Date updated | ☐ |

### 2.4 Reporting Effort Management

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.4.1 | Create Reporting Effort | 1. Click on `DBR-001` under `TEST-001`<br>2. Create Reporting Effort | Reporting effort created | ☐ |
| 2.4.2 | Create second effort | Create reporting effort for `DBR-002` | Effort created | ☐ |
| 2.4.3 | Create effort Study 2 | Create reporting effort for `DBR-001` under `TEST-002` | Effort created | ☐ |

### 2.5 Deletion Protection Tests

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.5.1 | Delete Study with children | Try to delete `TEST-001` | Error: Cannot delete - has dependent releases | ☐ |
| 2.5.2 | Delete Release with children | Try to delete `DBR-001` under `TEST-001` | Error: Cannot delete - has dependent efforts | ☐ |

---

## Phase 3: TFL Properties Management

### 3.1 Text Elements CRUD

**Login as:** `admin` (or `test_lead` - should also have access)

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 3.1.1 | Navigate to TFL Properties | Click "TFL Properties" in sidebar | TFL Properties page loads | ☐ |
| 3.1.2 | Create Title 1 | 1. Select "Title" tab<br>2. Click Add<br>3. Label: `Safety Summary`<br>4. Content: `Summary of Treatment-Emergent Adverse Events`<br>5. Save | Title created | ☐ |
| 3.1.3 | Create Title 2 | Add `Efficacy Summary` / `Summary of Primary Efficacy Endpoints` | Title created | ☐ |
| 3.1.4 | Create Footnotes | Switch to Footnotes tab, create:<br>- `AE Source` / `Source: Adverse Events dataset (ADAE)`<br>- `Inclusion` / `Includes all randomized subjects` | Both created | ☐ |
| 3.1.5 | Create Population Sets | Create `SAFFL` / `Safety Population` and `ITTFL` / `Intent-to-Treat Population` | Both created | ☐ |
| 3.1.6 | Create Acronyms | Create `AE` / `Adverse Event` and `SAE` / `Serious Adverse Event` | Both created | ☐ |
| 3.1.7 | Create ICH Category | Create `ICH_11.4` / `Extent of Exposure` | Created | ☐ |

### 3.2 Duplicate Text Element Validation

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 3.2.1 | Duplicate title | Try to create another `Safety Summary` title | Error: Label already exists | ☐ |
| 3.2.2 | Duplicate acronym | Try to create another `AE` acronym | Error: Label already exists | ☐ |

### 3.3 Text Element Update/Delete

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 3.3.1 | Update text element | Edit `AE Source` footnote, change content | Content updated | ☐ |
| 3.3.2 | Delete unused element | Create temp element `TEMP`, then delete it | Element deleted | ☐ |

---

## Phase 4: Package Management

### 4.1 Package CRUD

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 4.1.1 | Navigate to Packages | Click "Packages" in sidebar | Packages page loads | ☐ |
| 4.1.2 | Create Package 1 | Add package:<br>- Name: `PKG-SAFETY-001`<br>- Indication: `Type 2 Diabetes`<br>- Therapeutic Area: `Metabolic` | Package created | ☐ |
| 4.1.3 | Create Package 2 | Add `PKG-EFFICACY-001` with same indication/area | Package created | ☐ |
| 4.1.4 | Duplicate package | Try to create `PKG-SAFETY-001` again | Error: Package name exists | ☐ |
| 4.1.5 | Update package | Edit `PKG-SAFETY-001`, change indication | Updated | ☐ |

### 4.2 Package Items (TLF)

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 4.2.1 | Open package items | Click on `PKG-SAFETY-001` | Package items view opens | ☐ |
| 4.2.2 | Add Table item | Add TLF item:<br>- Code: `T-14.1.1`<br>- Description: `Summary of AEs`<br>- Type: TLF, Subtype: Table<br>- Title: `Safety Summary`<br>- Population: `SAFFL` | Item created | ☐ |
| 4.2.3 | Add Listing item | Add `L-16.1.1` / `Subject Listing` / Listing | Item created | ☐ |
| 4.2.4 | Add Figure item | Add `F-14.1.1` / `Forest Plot of AEs` / Figure | Item created | ☐ |
| 4.2.5 | Duplicate item code | Try to add `T-14.1.1` again | Error: Item code exists | ☐ |

### 4.3 Package Items (Dataset)

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 4.3.1 | Add Dataset item | Add Dataset item:<br>- Code: `ADAE`<br>- Description: `Analysis Dataset for AEs`<br>- Subtype: ADaM | Item created | ☐ |
| 4.3.2 | Add second dataset | Add `ADSL` / `Subject Level Analysis Dataset` / ADaM | Item created | ☐ |

### 4.4 Package Item Footnotes & Acronyms

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 4.4.1 | Add footnotes to item | Edit `T-14.1.1`, add footnotes: `AE Source`, `Inclusion` | Footnotes attached | ☐ |
| 4.4.2 | Add acronyms to item | Add acronyms: `AE`, `SAE` to same item | Acronyms attached | ☐ |
| 4.4.3 | Verify display | View item details | All attachments shown | ☐ |

---

## Phase 5: Tracker Workflow

### 5.1 Copy Package to Reporting Effort

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.1.1 | Navigate to reporting effort | Go to `TEST-001` → `DBR-001` → Reporting Effort | Items page loads | ☐ |
| 5.1.2 | Copy from package | Use "Copy from Package" feature, select `PKG-SAFETY-001` | Items copied to reporting effort | ☐ |
| 5.1.3 | Verify items | Check that all package items appear | All TLF and Dataset items present | ☐ |

### 5.2 Tracker Initial State

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.2.1 | View tracker | Click on Tracker tab/view | Tracker dashboard loads | ☐ |
| 5.2.2 | Check initial status | Verify all items show:<br>- Production: Not Started<br>- QC: Not Started | All statuses correct | ☐ |

### 5.3 Programmer Assignment

**Login as:** `admin` or `test_lead`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.3.1 | Assign production programmer | On `T-14.1.1`, assign `test_prog1` as Production Programmer | Programmer assigned | ☐ |
| 5.3.2 | Assign QC programmer | Assign `test_prog2` as QC Programmer | Programmer assigned | ☐ |
| 5.3.3 | Same programmer check | Try to assign `test_prog1` as both Prod and QC | Error: Same person cannot be both | ☐ |
| 5.3.4 | Bulk assign | Select multiple items, bulk assign `test_prog1` as Prod | All items updated | ☐ |

### 5.4 Production Status Workflow

**Login as:** `test_prog1` (assigned production programmer)

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.4.1 | Start production | Change `T-14.1.1` status to "In Progress" | Status changed | ☐ |
| 5.4.2 | Set Ready for QC | Change status to "Ready for QC" | Status changed | ☐ |
| 5.4.3 | Blocked: Set Completed | Try to manually set Production to "Completed" | Error: Cannot manually set Completed | ☐ |

### 5.5 QC Status Workflow

**Login as:** `test_prog2` (assigned QC programmer)

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.5.1 | Start QC | Change QC status to "In Progress" | Status changed | ☐ |
| 5.5.2 | Mark QC Failed | Change QC status to "Failed" | - QC: Failed<br>- Production auto-changes to "In Progress" | ☐ |
| 5.5.3 | Verify auto-trigger | Check Production status | Production is "In Progress" (auto-triggered) | ☐ |

### 5.6 Re-work After QC Failure

**Login as:** `test_prog1`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.6.1 | Fix and resubmit | Change Production back to "Ready for QC" | - Production: Ready for QC<br>- QC auto-changes to "In Progress" | ☐ |

### 5.7 QC Completion Flow

**Login as:** `test_prog2`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.7.1 | Complete QC | Change QC status to "Completed" | - QC: Completed<br>- Production auto-changes to "Completed" | ☐ |
| 5.7.2 | Verify both complete | Check both statuses | Both show "Completed" | ☐ |
| 5.7.3 | Set In Production flag | Toggle "In Production" flag to true | Flag set | ☐ |

### 5.8 Status Validation Rules

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.8.1 | No programmer validation | Create new tracker item, try to change status without programmer | Error: Programmer required | ☐ |
| 5.8.2 | Past due date | Set due date to yesterday | Error: Due date cannot be in past | ☐ |
| 5.8.3 | In Production flag locked | On incomplete item, try to set In Production | Error: Both must be Completed | ☐ |

---

## Phase 6: Comments & Notifications

### 6.1 Add Comments to Tracker

**Login as:** `test_prog1`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 6.1.1 | Open comments | Click comments icon on `T-14.1.1` | Comments panel opens | ☐ |
| 6.1.2 | Add GENERAL comment | Add comment: "Starting work on this table" Type: GENERAL | Comment added | ☐ |
| 6.1.3 | Add QUESTION comment | Add: "Need clarification on population" Type: QUESTION | Comment added as unresolved | ☐ |
| 6.1.4 | Add ISSUE comment | Add: "Missing source data" Type: ISSUE | Comment added as unresolved | ☐ |

### 6.2 Comment Resolution

**Login as:** `test_prog2`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 6.2.1 | View comments | Open comments on same tracker | All comments visible | ☐ |
| 6.2.2 | Reply to question | Add reply to QUESTION comment | Reply attached to parent | ☐ |
| 6.2.3 | Resolve comment | Mark QUESTION comment as resolved | Comment shows as resolved | ☐ |
| 6.2.4 | QC blocked by comments | Try to mark QC as Completed with unresolved ISSUE | Error: Unresolved comments exist | ☐ |
| 6.2.5 | Resolve all | Resolve all remaining comments | All resolved | ☐ |
| 6.2.6 | QC can complete | Now mark QC as Completed | Status changes successfully | ☐ |

### 6.3 Notifications

**Login as:** `test_prog1` (in Browser 1)

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 6.3.1 | Check notification bell | Look at notification icon in header | Shows notification count | ☐ |
| 6.3.2 | View notifications | Click bell icon | Notifications dropdown shows | ☐ |
| 6.3.3 | Assignment notification | Check for "You've been assigned as Production Programmer" | Notification present | ☐ |
| 6.3.4 | Mark as read | Click on notification | Marked as read, count decreases | ☐ |
| 6.3.5 | Acknowledge | Dismiss notification | Notification removed | ☐ |

---

## Phase 7: Role-Based Access Control

### 7.1 Admin Access (Full)

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 7.1.1 | User Management | Access User Management | Full access | ☐ |
| 7.1.2 | Database Backup | Access Database Backup | Full access | ☐ |
| 7.1.3 | Audit Logs | Access Audit Logs | Full access | ☐ |
| 7.1.4 | Settings | Access Settings | Full access | ☐ |
| 7.1.5 | All Studies | Can see all studies | All studies visible | ☐ |
| 7.1.6 | Director Dashboard | Access Director Dashboard | Full access | ☐ |

### 7.2 LEAD Access (Study-Scoped Admin)

**Login as:** `test_lead`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 7.2.1 | Assigned study visible | Check study list | `TEST-001` visible | ☐ |
| 7.2.2 | Unassigned study hidden | Check study list | `TEST-002` not visible (or read-only) | ☐ |
| 7.2.3 | Can manage study | Edit study `TEST-001` details | Allowed | ☐ |
| 7.2.4 | Can manage releases | Add/edit database releases | Allowed | ☐ |
| 7.2.5 | Can manage members | Access study members dialog | Allowed | ☐ |
| 7.2.6 | Can assign programmers | Bulk assign programmers | Allowed | ☐ |
| 7.2.7 | Can manage packages | Access Packages page | Allowed | ☐ |
| 7.2.8 | Can manage TFL properties | Access TFL Properties | Allowed | ☐ |
| 7.2.9 | NO User Management | Try to access User Management | Not accessible/hidden | ☐ |
| 7.2.10 | NO Database Backup | Try to access Database Backup | Not accessible/hidden | ☐ |
| 7.2.11 | NO Audit Logs | Try to access Audit Logs | Not accessible/hidden | ☐ |
| 7.2.12 | NO Director Dashboard | Try to access Director Dashboard | Not accessible/hidden | ☐ |

### 7.3 EDITOR Access (Assigned Items Only)

**Login as:** `test_editor`

First, have admin assign `test_editor` as Production Programmer on `T-14.1.1`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 7.3.1 | Can view study | Navigate to `TEST-001` | Can view | ☐ |
| 7.3.2 | Can view tracker | View tracker items | Can view all items | ☐ |
| 7.3.3 | Can edit assigned item | Change status on `T-14.1.1` (assigned) | Allowed | ☐ |
| 7.3.4 | Cannot edit unassigned | Try to change status on other items | Not allowed | ☐ |
| 7.3.5 | Cannot assign programmers | Try to use bulk assign | Button hidden/disabled | ☐ |
| 7.3.6 | Cannot delete items | Try to delete tracker item | Button hidden/disabled | ☐ |
| 7.3.7 | NO Package management | Try to access Packages | Not accessible/hidden | ☐ |
| 7.3.8 | NO TFL Properties | Try to access TFL Properties | Not accessible/hidden | ☐ |

### 7.4 VIEWER Access (Read-Only)

**Login as:** `test_viewer`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 7.4.1 | Can view study | Navigate to `TEST-001` | Can view | ☐ |
| 7.4.2 | Can view releases | View database releases | Can view | ☐ |
| 7.4.3 | Can view tracker | View tracker items | Can view | ☐ |
| 7.4.4 | Cannot edit anything | Try to change any tracker status | All edit controls hidden/disabled | ☐ |
| 7.4.5 | Cannot add comments | Try to add comment | Not allowed | ☐ |
| 7.4.6 | No edit buttons | Check for edit/delete buttons | All hidden | ☐ |

### 7.5 Cross-Study Access

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 7.5.1 | LEAD cannot access other study | As `test_lead`, try to access `TEST-002` | Not allowed/not visible | ☐ |
| 7.5.2 | EDITOR cannot access other study | As `test_editor`, try to access `TEST-002` | Not allowed/not visible | ☐ |
| 7.5.3 | Admin can access all | As `admin`, access both studies | Full access to both | ☐ |

---

## Phase 8: Real-Time Updates (WebSocket)

### Setup
Open **two browser windows/tabs** side by side:
- **Browser 1:** Login as `admin`
- **Browser 2:** Login as `test_lead`

Both navigate to `TEST-001` tracker view.

### 8.1 Real-Time Sync Tests

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 8.1.1 | Status update sync | In Browser 1, change a tracker status | Browser 2 shows update without refresh | ☐ |
| 8.1.2 | Programmer assignment sync | In Browser 1, assign programmer | Browser 2 shows new assignment | ☐ |
| 8.1.3 | Comment sync | In Browser 1, add a comment | Browser 2 shows new comment count | ☐ |
| 8.1.4 | New item sync | In Browser 1, create new tracker item | Browser 2 shows new item | ☐ |
| 8.1.5 | Delete sync | In Browser 1, delete an item | Item disappears in Browser 2 | ☐ |

### 8.2 Cross-Entity Updates

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 8.2.1 | Study update sync | In Browser 1 (admin), rename study | Browser 2 shows new name | ☐ |
| 8.2.2 | Release update sync | Add new database release | Browser 2 shows new release | ☐ |
| 8.2.3 | User update sync | In Browser 1 (admin), update a user | Changes reflect immediately | ☐ |

### 8.3 Reconnection Test

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 8.3.1 | Network disconnect | Disable network briefly, then re-enable | WebSocket reconnects automatically | ☐ |
| 8.3.2 | Sync after reconnect | After reconnect, make change in Browser 1 | Browser 2 receives update | ☐ |

---

## Phase 9: Business Rule Validation

### 9.1 Duplicate Entry Prevention

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 9.1.1 | Duplicate study | Create study with existing label | Error displayed | ☐ |
| 9.1.2 | Duplicate release | Create release with existing label in same study | Error displayed | ☐ |
| 9.1.3 | Duplicate package | Create package with existing name | Error displayed | ☐ |
| 9.1.4 | Duplicate item code | Create package item with existing code | Error displayed | ☐ |
| 9.1.5 | Duplicate text element | Create text element with existing label (same type) | Error displayed | ☐ |
| 9.1.6 | Duplicate username | Create user with existing username | Error displayed | ☐ |

### 9.2 Cascade/Dependency Rules

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 9.2.1 | Delete study with releases | Try to delete study with releases | Blocked: "Has X dependent releases" | ☐ |
| 9.2.2 | Delete release with efforts | Try to delete release with efforts | Blocked: "Has X dependent efforts" | ☐ |
| 9.2.3 | Delete package with items | Try to delete package with items | Blocked: "Has X dependent items" | ☐ |
| 9.2.4 | Delete text element in use | Try to delete title used in package item | Blocked or warned | ☐ |

### 9.3 Tracker Validation Rules

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 9.3.1 | Same programmer check | Assign same person as Prod and QC | Error: Cannot be same person | ☐ |
| 9.3.2 | Status without programmer | Change status from Not Started without programmer | Error: Programmer required | ☐ |
| 9.3.3 | QC Completed with comments | Try QC Completed with unresolved comments | Error: Unresolved comments | ☐ |
| 9.3.4 | Production Completed manual | Try to manually set Production to Completed | Error: Can only be auto-set | ☐ |
| 9.3.5 | QC status requires Prod Ready | Try to set QC to Completed when Prod is In Progress | Error: Production must be Ready for QC | ☐ |
| 9.3.6 | In Production flag locked | Set In Production when not both Completed | Error: Both must be Completed | ☐ |
| 9.3.7 | Past due date | Set due date to yesterday (incomplete task) | Error: Due date cannot be in past | ☐ |

---

## Phase 10: Audit Trail Verification

### 10.1 Audit Log Access

**Login as:** `admin`

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 10.1.1 | Access audit logs | Navigate to Audit Logs page | Page loads with log entries | ☐ |
| 10.1.2 | Filter by action | Filter by "CREATE" | Only CREATE actions shown | ☐ |
| 10.1.3 | Filter by entity | Filter by "study" | Only study records shown | ☐ |
| 10.1.4 | Filter by user | Filter by "admin" | Only admin's actions shown | ☐ |
| 10.1.5 | Date range filter | Set date range to today | Only today's entries shown | ☐ |

### 10.2 Audit Entry Verification

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 10.2.1 | Study create logged | Find study `TEST-001` creation | Entry exists with CREATE action | ☐ |
| 10.2.2 | User create logged | Find user creation entries | All test users logged | ☐ |
| 10.2.3 | Update logged | Find an update entry | Shows old/new values in changes | ☐ |
| 10.2.4 | IP address captured | Check any entry | IP address recorded | ☐ |
| 10.2.5 | User agent captured | Check any entry | Browser info recorded | ☐ |

### 10.3 Non-Admin Audit Access

| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 10.3.1 | LEAD cannot access | Login as `test_lead`, try Audit Logs | Not accessible | ☐ |
| 10.3.2 | EDITOR cannot access | Login as `test_editor`, try Audit Logs | Not accessible | ☐ |
| 10.3.3 | VIEWER cannot access | Login as `test_viewer`, try Audit Logs | Not accessible | ☐ |

---

## Test Results Summary

### Quick Stats

| Phase | Total Tests | Passed | Failed | Blocked |
|-------|-------------|--------|--------|---------|
| 1. User Management | 13 | | | |
| 2. Core Hierarchy | 17 | | | |
| 3. TFL Properties | 10 | | | |
| 4. Package Management | 12 | | | |
| 5. Tracker Workflow | 20 | | | |
| 6. Comments & Notifications | 12 | | | |
| 7. Role-Based Access | 25 | | | |
| 8. Real-Time Updates | 10 | | | |
| 9. Business Rules | 15 | | | |
| 10. Audit Trail | 11 | | | |
| **TOTAL** | **145** | | | |

### Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | | | |
| Reviewer | | | |
| Approver | | | |

### Issues Found

| Issue # | Phase | Test # | Description | Severity | Status |
|---------|-------|--------|-------------|----------|--------|
| | | | | | |
| | | | | | |
| | | | | | |

### Notes

---

## Appendix A: Test Data Cleanup

After testing, run these cleanup steps (as admin):

1. Delete test reporting efforts
2. Delete test database releases
3. Delete test studies (`TEST-001`, `TEST-002`)
4. Delete test packages
5. Delete test text elements
6. Delete test users (keep admin)

Or, restore from a database backup taken before testing.

---

## Appendix B: Quick Reference - Tracker Status Flow

```
PRODUCTION:
  Not Started → In Progress → Ready for QC → Completed (AUTO ONLY)
                     ↑                            ↓
                     └──── (QC Failed triggers) ──┘

QC:
  Not Started → In Progress → Failed/Completed
                     ↑            ↓
                     └────────────┘ (Prod resubmit triggers In Progress)

AUTO-TRIGGERS:
  - QC Completed → Production Completed
  - QC Failed → Production In Progress
  - Production Ready for QC (when QC was Failed) → QC In Progress
```

---

## Appendix C: Role Permissions Matrix

| Feature | Admin | LEAD | EDITOR (assigned) | VIEWER |
|---------|-------|------|-------------------|--------|
| User Management | ✅ | ❌ | ❌ | ❌ |
| Database Backup | ✅ | ❌ | ❌ | ❌ |
| Audit Logs | ✅ | ❌ | ❌ | ❌ |
| Settings | ✅ | ❌ | ❌ | ❌ |
| Director Dashboard | ✅ | ❌ | ❌ | ❌ |
| Create/Delete Study | ✅ | ❌ | ❌ | ❌ |
| Edit Study | ✅ | ✅ (own) | ❌ | ❌ |
| Manage DB Releases | ✅ | ✅ (own) | ❌ | ❌ |
| Manage Packages | ✅ | ✅ | ❌ | ❌ |
| Manage TFL Properties | ✅ | ✅ | ❌ | ❌ |
| Assign Programmers | ✅ | ✅ | ❌ | ❌ |
| Bulk Status Update | ✅ | ✅ | ❌ | ❌ |
| Edit Assigned Tracker | ✅ | ✅ | ✅ | ❌ |
| Add Comments | ✅ | ✅ | ✅ | ❌ |
| View Tracker | ✅ | ✅ | ✅ | ✅ |
| View Study | ✅ | ✅ (own) | ✅ (own) | ✅ (own) |

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Application: PEARL (Package, Effort and Analysis Reporting Library)*
