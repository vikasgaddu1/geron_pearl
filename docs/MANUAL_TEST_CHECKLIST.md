# PEARL Manual Test Checklist v2.0

**Tester:** _________________ **Date:** _________________ **Environment:** ☐ Local ☐ Railway

**Pre-flight Run:** ☐ Pass ☐ Fail  **Browser:** _________________

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 🤖 | **Automated** - Pre-verified by `test_preflight_comprehensive.sh` |
| 👁️ | **Manual Only** - Requires human verification (UI, visual, multi-browser) |
| ⚠️ | **Critical** - Security or data integrity test |

## How to Record Findings

1. **For each test:** Mark ☐ as ☑ (pass) or ☒ (fail)
2. **If a test fails:** Record in the **TESTER FINDINGS** section at the end
3. **For observations:** Use the **UI/UX Observations** section
4. **Add notes:** Use **Additional Notes** for anything else

---

## Pre-Test Requirements

1. **Run Automated Pre-flight Tests First:**
   ```bash
   cd backend
   ./tests/scripts/test_preflight_comprehensive.sh
   ```
   
2. If pre-flight passes, proceed with manual tests below (focus on 👁️ items)
3. If pre-flight fails, fix issues before manual testing

---

## PHASE 1: USER MANAGEMENT _(Login: admin)_

### Create Users
| # | Test | Data | Pre-verified | Manual Check |
|---|------|------|--------------|--------------|
| 1 | Create LEAD user | `test_lead` / `LeadPass123!` | 🤖 | ☐ UI shows user |
| 2 | Create EDITOR user | `test_editor` / `EditorPass123!` | 🤖 | ☐ UI shows user |
| 3 | Create VIEWER user | `test_viewer` / `ViewerPass123!` | 🤖 | ☐ UI shows user |
| 4 | Create prog1 | `test_prog1` / `Prog1Pass123!` | 🤖 | ☐ UI shows user |
| 5 | Create prog2 | `test_prog2` / `Prog2Pass123!` | 🤖 | ☐ UI shows user |

### Validation (All Automated 🤖)
| # | Test | Expected | Pass |
|---|------|----------|------|
| 6 | ⚠️ Duplicate username | Error message | 🤖 |
| 7 | ⚠️ Duplicate email | Error message | 🤖 |
| 8 | Valid login | Redirect to dashboard | 🤖 |
| 9 | Invalid password | Error message | 🤖 |
| 10 | 👁️ Logout button | Redirect to login page | ☐ |

---

## PHASE 2: STUDY HIERARCHY _(Login: admin)_

### Studies
| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 11 | Create `TEST-001` | 🤖 | ☐ UI shows study |
| 12 | Create `TEST-002` | 🤖 | ☐ UI shows study |
| 13 | ⚠️ Duplicate blocked | 🤖 | ☐ Error displays nicely |

### Study Members (on TEST-001)
| # | User → Role | Pre-verified | Manual Check |
|---|-------------|--------------|--------------|
| 14 | `test_lead` → LEAD | 🤖 | ☐ Shows in members dialog |
| 15 | `test_editor` → EDITOR | 🤖 | ☐ Shows in members dialog |
| 16 | `test_viewer` → VIEWER | 🤖 | ☐ Shows in members dialog |
| 17 | `test_prog1` → EDITOR | 🤖 | ☐ Shows in members dialog |
| 18 | `test_prog2` → EDITOR | 🤖 | ☐ Shows in members dialog |

### Database Releases
| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 19 | Create DBR-001 (2026-01-15) | 🤖 | ☐ Shows in UI |
| 20 | Create DBR-002 (2026-02-15) | 🤖 | ☐ Shows in UI |
| 21 | ⚠️ Duplicate blocked | 🤖 | ☐ Error displays |
| 22 | Create DBR-001 on TEST-002 | 🤖 | ☐ Different study OK |

### Reporting Efforts & Deletion Protection
| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 23-25 | Create efforts | 🤖 | ☐ Shows in UI |
| 26 | ⚠️ Delete study blocked | 🤖 | ☐ Clear error message |
| 27 | ⚠️ Delete release blocked | 🤖 | ☐ Clear error message |

---

## PHASE 3: TFL PROPERTIES _(Admin or Lead)_

| # | Type/Label | Pre-verified | Manual Check |
|---|------------|--------------|--------------|
| 28-29 | Titles | 🤖 | ☐ Shows in list |
| 30-31 | Footnotes | 🤖 | ☐ Shows in list |
| 32-33 | Population Sets | 🤖 | ☐ Shows in list |
| 34-35 | Acronyms | 🤖 | ☐ Shows in list |
| 36 | ICH Category | 🤖 | ☐ Shows in list |
| 37 | ⚠️ Duplicate blocked | 🤖 | ☐ Error displays |

---

## PHASE 4: PACKAGES _(Admin)_

| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 38-39 | Create packages | 🤖 | ☐ Shows in list |
| 40 | ⚠️ Duplicate blocked | 🤖 | ☐ Error displays |
| 41-45 | Create items (TLF + Dataset) | 🤖 | ☐ Shows in package |
| 46 | ⚠️ Duplicate item code | 🤖 | ☐ Error displays |
| 47-48 | 👁️ Add footnotes/acronyms | — | ☐ UI selector works |

---

## PHASE 5: TRACKER WORKFLOW ⭐ HIGH PRIORITY

### Setup
| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 49 | 👁️ Copy package to effort | — | ☐ Items appear |
| 50 | 👁️ Verify 5 items copied | — | ☐ All items present |

### Programmer Assignment
| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 51 | Assign prod programmer | 🤖 | ☐ Name shows in UI |
| 52 | Assign QC programmer | 🤖 | ☐ Name shows in UI |
| 53 | ⚠️ Same programmer blocked | 🤖 | ☐ Clear error |

### Status Workflow (Critical Path - Login as assigned user)
| # | Action | Pre-verified | Manual Check |
|---|--------|--------------|--------------|
| 54 | Prod → In Progress | 🤖 | ☐ 👁️ Status badge updates |
| 55 | Prod → Ready for QC | 🤖 | ☐ 👁️ Status badge updates |
| 56 | ⚠️ Prod → Completed blocked | 🤖 | ☐ Error message |
| 57 | QC → In Progress | 🤖 | ☐ 👁️ Status badge updates |
| 58 | **QC → Failed** (AUTO-TRIGGER) | 🤖 | ☐ 👁️ Prod auto-reverts |
| 59 | **Prod → Ready** (AUTO-TRIGGER) | 🤖 | ☐ 👁️ QC auto-updates |
| 60 | **QC → Completed** (AUTO-TRIGGER) | 🤖 | ☐ 👁️ Prod auto-completes |
| 61 | 👁️ Set In Production flag | — | ☐ Flag toggles |

### Validation Rules
| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 62 | ⚠️ Status w/o programmer | 🤖 | ☐ Error message |
| 63 | ⚠️ Past due date | 🤖 | ☐ Error message |
| 64 | ⚠️ In Production locked | 🤖 | ☐ Button disabled |

---

## PHASE 6: COMMENTS & NOTIFICATIONS ⭐ MANUAL FOCUS

### Comments
| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 65 | Add GENERAL comment | 🤖 | ☐ 👁️ Shows in thread |
| 66 | Add QUESTION (unresolved) | 🤖 | ☐ 👁️ Shows unresolved badge |
| 67 | Add ISSUE (unresolved) | 🤖 | ☐ 👁️ Shows unresolved badge |
| 68 | 👁️ Reply to comment | — | ☐ Threaded reply shows |
| 69 | Resolve comment | 🤖 | ☐ 👁️ Badge changes |
| 70 | ⚠️ QC blocked by comments | — | ☐ Error message |
| 71-72 | Resolve all → QC completes | — | ☐ Workflow works |

### Notifications (All Manual 👁️)
| # | Test | Manual Check |
|---|------|--------------|
| 73 | 👁️ Bell icon shows count | ☐ Count visible |
| 74 | 👁️ Assignment notification | ☐ Notification exists |
| 75 | 👁️ Mark as read | ☐ Count decreases |
| 76 | 👁️ Dismiss notification | ☐ Notification removed |

---

## PHASE 7: ROLE-BASED ACCESS ⭐ SECURITY CRITICAL

### Admin Access
| # | Feature | Pre-verified | Manual Check |
|---|---------|--------------|--------------|
| 77-82 | Full admin access | 🤖 | ☐ 👁️ All menu items visible |

### LEAD Access _(Login: test_lead)_
| # | Feature | Expected | Pre-verified | Manual |
|---|---------|----------|--------------|--------|
| 83 | TEST-001 visible | Yes | — | ☐ |
| 84 | ⚠️ TEST-002 NOT visible | No | — | ☐ |
| 85-89 | Can manage own study | Yes | — | ☐ |
| 90 | ⚠️ User Management hidden | No | 🤖 | ☐ 👁️ Menu item hidden |
| 91 | ⚠️ Database Backup hidden | No | — | ☐ 👁️ Menu item hidden |
| 92 | ⚠️ Audit Logs hidden | No | 🤖 | ☐ 👁️ Menu item hidden |
| 93 | ⚠️ Director Dashboard hidden | No | — | ☐ 👁️ Menu item hidden |

### EDITOR Access _(Login: test_editor)_
| # | Feature | Expected | Manual Check |
|---|---------|----------|--------------|
| 94 | 👁️ View study | Yes | ☐ |
| 95 | 👁️ View tracker | Yes | ☐ |
| 96 | 👁️ Edit assigned item | Yes | ☐ |
| 97 | ⚠️ 👁️ Edit unassigned blocked | No | ☐ Button disabled |
| 98 | ⚠️ 👁️ Assign programmers hidden | No | ☐ Button hidden |
| 99 | ⚠️ 👁️ Delete items hidden | No | ☐ Button hidden |
| 100 | ⚠️ 👁️ Packages hidden | No | ☐ Menu hidden |

### VIEWER Access _(Login: test_viewer)_
| # | Feature | Expected | Manual Check |
|---|---------|----------|--------------|
| 101-102 | 👁️ View study/tracker | Yes | ☐ |
| 103 | ⚠️ 👁️ Edit controls hidden | All hidden | ☐ |
| 104 | ⚠️ 👁️ Add comments disabled | Disabled | ☐ |

---

## PHASE 8: REAL-TIME (WebSocket) ⭐ ALL MANUAL

**Setup:** Two browsers side-by-side, both logged in

| # | Action (Browser 1) | Browser 2 Result | Pass |
|---|-------------------|------------------|------|
| 105 | 👁️ Change tracker status | Updates instantly | ☐ |
| 106 | 👁️ Assign programmer | Updates instantly | ☐ |
| 107 | 👁️ Add comment | Count updates | ☐ |
| 108 | 👁️ Create new item | Item appears | ☐ |
| 109 | 👁️ Delete item | Item disappears | ☐ |
| 110 | 👁️ Disconnect network, reconnect | Auto-reconnects | ☐ |

---

## PHASE 9: BUSINESS RULES (Mostly Automated)

| # | Rule | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 111-116 | ⚠️ Duplicate prevention | 🤖 | ☐ Errors display nicely |
| 117-119 | ⚠️ Cascade protection | 🤖 | ☐ Errors display nicely |
| 120-125 | ⚠️ Tracker rules | 🤖 | ☐ Errors display nicely |

---

## PHASE 10: AUDIT TRAIL

| # | Test | Pre-verified | Manual Check |
|---|------|--------------|--------------|
| 126-130 | Filter/search | 🤖 | ☐ 👁️ UI filters work |
| 131-134 | 👁️ Data quality | — | ☐ Changes logged correctly |
| 135 | ⚠️ Non-admin blocked | 🤖 | ☐ 👁️ Menu hidden |

---

## SUMMARY

### Test Coverage

| Category | Total | Automated 🤖 | Manual Only 👁️ |
|----------|-------|--------------|-----------------|
| User Management | 10 | 9 | 1 |
| Study Hierarchy | 17 | 15 | 2 |
| TFL Properties | 10 | 10 | 0 |
| Packages | 11 | 9 | 2 |
| Tracker Workflow | 16 | 12 | 4 |
| Comments/Notifications | 12 | 4 | 8 |
| Role Access | 22 | 4 | 18 |
| Real-Time (WebSocket) | 6 | 0 | 6 |
| Business Rules | 15 | 15 | 0 |
| Audit Trail | 10 | 6 | 4 |
| **TOTAL** | **129** | **~84 (65%)** | **~45 (35%)** |

### Results

| Category | Passed | Failed |
|----------|--------|--------|
| Automated (pre-flight) | | |
| Manual verification | | |
| **Total** | | |

---

## ISSUES FOUND

| # | Phase | Test | Description | Severity | Status |
|---|-------|------|-------------|----------|--------|
| | | | | | |
| | | | | | |

---

## Quick Reference: What Human Testers Should Focus On

### 1. **UI/Visual Verification** (after automated tests pass)
- Do error messages display clearly?
- Are buttons/menus hidden appropriately per role?
- Do status badges update correctly?

### 2. **Multi-Browser WebSocket Tests** (Phase 8)
- Real-time sync between users
- Reconnection after network issues

### 3. **Role Permission UI** (Phase 7)
- Menu items hidden/shown correctly
- Buttons disabled for restricted users
- Can't access other users' studies

### 4. **Notifications UI** (Phase 6)
- Bell icon count
- Mark as read/dismiss
- Assignment notifications

### 5. **Complex Workflows**
- Copy package to effort
- Comment threading and resolution
- QC blocked by unresolved comments

---

## TESTER FINDINGS & ISSUES

### Critical Issues (Blocking)
| # | Test Ref | Description | Steps to Reproduce | Severity |
|---|----------|-------------|-------------------|----------|
| 1 | | | | ☐ Critical ☐ High |
| 2 | | | | ☐ Critical ☐ High |
| 3 | | | | ☐ Critical ☐ High |
| 4 | | | | ☐ Critical ☐ High |
| 5 | | | | ☐ Critical ☐ High |

### Non-Critical Issues
| # | Test Ref | Description | Expected vs Actual | Severity |
|---|----------|-------------|-------------------|----------|
| 1 | | | | ☐ Medium ☐ Low |
| 2 | | | | ☐ Medium ☐ Low |
| 3 | | | | ☐ Medium ☐ Low |
| 4 | | | | ☐ Medium ☐ Low |
| 5 | | | | ☐ Medium ☐ Low |
| 6 | | | | ☐ Medium ☐ Low |
| 7 | | | | ☐ Medium ☐ Low |
| 8 | | | | ☐ Medium ☐ Low |

### UI/UX Observations
| # | Location | Observation | Suggestion |
|---|----------|-------------|------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### Additional Notes
```
_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________
```

---

## TEST SUMMARY

| Category | Total | Passed | Failed | Skipped |
|----------|-------|--------|--------|---------|
| User Management | | | | |
| Study Hierarchy | | | | |
| TFL Properties | | | | |
| Packages | | | | |
| Tracker Workflow | | | | |
| Comments | | | | |
| Notifications | | | | |
| Role Permissions | | | | |
| WebSocket | | | | |
| **TOTAL** | | | | |

**Overall Result:** ☐ PASS ☐ PASS WITH ISSUES ☐ FAIL

---

**Pre-flight Completed:** ☐ Yes ☐ No (If No, run it first!)

**Tester Signature:** _________________________ **Date:** _____________

**Reviewed By:** _________________________ **Date:** _____________
