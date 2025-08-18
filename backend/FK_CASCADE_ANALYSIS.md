# Foreign Key Cascade Analysis and Migration Plan

## Overview
This document provides a comprehensive analysis of the current foreign key constraints in the PEARL database and outlines the migration plan to fix cascade delete issues that are causing orphaned records.

## Current Foreign Key Constraints Analysis

### 1. Study-Related Constraints (⚠️ CRITICAL ISSUES)

```sql
-- MISSING CASCADE DELETE - This is causing orphaned data
database_releases_study_id_fkey FOREIGN KEY (study_id) REFERENCES public.studies(id);
reporting_efforts_study_id_fkey FOREIGN KEY (study_id) REFERENCES public.studies(id);
```

**Impact**: When a study is deleted directly from database, it leaves orphaned records in:
- `database_releases` table
- `reporting_efforts` table
- All downstream tables (items, trackers, comments)

### 2. Database Release Constraints

```sql
-- MISSING CASCADE DELETE
reporting_efforts_database_release_id_fkey FOREIGN KEY (database_release_id) REFERENCES public.database_releases(id);
```

**Impact**: Deleting database release leaves orphaned reporting efforts

### 3. Package System Constraints

```sql
-- MISSING CASCADE DELETE
package_items_package_id_fkey FOREIGN KEY (package_id) REFERENCES public.packages(id);
package_tlf_details_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES public.package_items(id);
package_dataset_details_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES public.package_items(id);
package_item_footnotes_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES public.package_items(id);
package_item_acronyms_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES public.package_items(id);
```

**Impact**: Package deletion leaves orphaned items and details

### 4. Reporting Effort System Constraints

```sql
-- MISSING CASCADE DELETE - Mismatch with SQLAlchemy
reporting_effort_items_reporting_effort_id_fkey FOREIGN KEY (reporting_effort_id) REFERENCES public.reporting_efforts(id);
reporting_effort_item_tracker_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);
reporting_effort_tlf_details_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);
reporting_effort_dataset_details_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);
reporting_effort_item_footnotes_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);
reporting_effort_item_acronyms_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES public.reporting_effort_items(id);
```

### 5. User-Related Constraints (⚠️ REQUIRES CAREFUL HANDLING)

```sql
-- MISSING CASCADE/SET NULL - Need to decide on behavior
audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);
reporting_effort_item_tracker_production_programmer_id_fkey FOREIGN KEY (production_programmer_id) REFERENCES public.users(id);
reporting_effort_item_tracker_qc_programmer_id_fkey FOREIGN KEY (qc_programmer_id) REFERENCES public.users(id);
tracker_comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);
tracker_comments_resolved_by_user_id_fkey FOREIGN KEY (resolved_by_user_id) REFERENCES public.users(id);
```

### 6. Text Element References

```sql
-- MISSING CASCADE/SET NULL
package_tlf_details_title_id_fkey FOREIGN KEY (title_id) REFERENCES public.text_elements(id);
package_tlf_details_population_flag_id_fkey FOREIGN KEY (population_flag_id) REFERENCES public.text_elements(id);
package_tlf_details_ich_category_id_fkey FOREIGN KEY (ich_category_id) REFERENCES public.text_elements(id);
package_item_footnotes_footnote_id_fkey FOREIGN KEY (footnote_id) REFERENCES public.text_elements(id);
package_item_acronyms_acronym_id_fkey FOREIGN KEY (acronym_id) REFERENCES public.text_elements(id);
-- Similar for reporting_effort tables...
```

### 7. Correctly Configured Constraints ✅

```sql
-- These are ALREADY correct
tracker_comments_parent_comment_id_fkey FOREIGN KEY (parent_comment_id) REFERENCES public.tracker_comments(id) ON DELETE CASCADE;
tracker_comments_tracker_id_fkey FOREIGN KEY (tracker_id) REFERENCES public.reporting_effort_item_tracker(id) ON DELETE CASCADE;
```

## SQLAlchemy vs Database Constraint Mismatches

### Critical Mismatches:

1. **ReportingEffort.items** - SQLAlchemy has `cascade="all, delete-orphan"` but database has no CASCADE
2. **ReportingEffortItem.tracker** - SQLAlchemy has `cascade="all, delete-orphan"` but database has no CASCADE
3. **User.comments** - SQLAlchemy has `cascade="all, delete-orphan"` but database has no CASCADE

## Risk Assessment

### High Risk Changes:
- Study cascade changes (affects many tables)
- User cascade changes (could affect audit trails)

### Medium Risk Changes:
- Package cascade changes
- Database release cascade changes

### Low Risk Changes:
- Detail table cascades (already isolated)
- Comment system cascades (already partially implemented)

## Migration Strategy

### Phase 1: Data Cleanup (REQUIRED BEFORE CONSTRAINTS)
- Identify and handle all orphaned records
- Cannot add CASCADE constraints while orphaned data exists

### Phase 2: Constraint Updates
- Update constraints in dependency order (bottom-up)
- Test each constraint change individually

### Phase 3: Validation
- Comprehensive testing of cascade behavior
- Rollback procedures for each step

## Next Steps
1. Use database tools to identify orphaned records
2. Create cleanup scripts
3. Generate migration SQL scripts
4. Test in staging environment

---
**Status**: Analysis Phase - Document Created
**Next Action**: Begin orphaned data identification
