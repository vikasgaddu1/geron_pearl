"""Add CASCADE DELETE constraints to fix orphaned records issue

Revision ID: add_cascade_delete_constraints
Revises: 07fb820f6a75
Create Date: 2025-01-18 16:45:00.000000

This migration addresses the critical foreign key constraint issues that cause
orphaned records when parent entities are deleted. The migration:

1. Updates study-related constraints with CASCADE DELETE
2. Updates database release constraints with CASCADE DELETE  
3. Updates package-related constraints with CASCADE DELETE
4. Updates reporting effort chain constraints with CASCADE DELETE
5. Updates user-related constraints with SET NULL or RESTRICT as appropriate
6. Updates detail table constraints with CASCADE DELETE

IMPORTANT: This migration has been tested with clean data (no orphaned records).
If orphaned records exist, they must be cleaned up before running this migration.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_cascade_delete_constraints'
down_revision = 'f5a535fcf5e5'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """
    Add CASCADE DELETE constraints to prevent orphaned records.
    
    The order of operations is important to avoid constraint conflicts.
    """
    
    print("🚀 Starting CASCADE DELETE constraints migration...")
    
    # ========================================================================
    # PHASE 1: Study-Related Constraints (CRITICAL - fixes the main issue)
    # ========================================================================
    
    print("📋 Phase 1: Updating study-related constraints...")
    
    # 1.1: Update database_releases.study_id constraint
    print("  - Updating database_releases.study_id constraint...")
    op.execute("ALTER TABLE database_releases DROP CONSTRAINT database_releases_study_id_fkey")
    op.execute("""
        ALTER TABLE database_releases 
        ADD CONSTRAINT database_releases_study_id_fkey 
        FOREIGN KEY (study_id) REFERENCES studies(id) ON DELETE CASCADE
    """)
    
    # 1.2: Update reporting_efforts.study_id constraint
    print("  - Updating reporting_efforts.study_id constraint...")
    op.execute("ALTER TABLE reporting_efforts DROP CONSTRAINT reporting_efforts_study_id_fkey")
    op.execute("""
        ALTER TABLE reporting_efforts 
        ADD CONSTRAINT reporting_efforts_study_id_fkey 
        FOREIGN KEY (study_id) REFERENCES studies(id) ON DELETE CASCADE
    """)
    
    # ========================================================================
    # PHASE 2: Database Release Constraints
    # ========================================================================
    
    print("📋 Phase 2: Updating database release constraints...")
    
    # 2.1: Update reporting_efforts.database_release_id constraint
    print("  - Updating reporting_efforts.database_release_id constraint...")
    op.execute("ALTER TABLE reporting_efforts DROP CONSTRAINT reporting_efforts_database_release_id_fkey")
    op.execute("""
        ALTER TABLE reporting_efforts 
        ADD CONSTRAINT reporting_efforts_database_release_id_fkey 
        FOREIGN KEY (database_release_id) REFERENCES database_releases(id) ON DELETE CASCADE
    """)
    
    # ========================================================================
    # PHASE 3: Reporting Effort Chain Constraints
    # ========================================================================
    
    print("📋 Phase 3: Updating reporting effort chain constraints...")
    
    # 3.1: Update reporting_effort_items.reporting_effort_id constraint
    print("  - Updating reporting_effort_items.reporting_effort_id constraint...")
    op.execute("ALTER TABLE reporting_effort_items DROP CONSTRAINT reporting_effort_items_reporting_effort_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_items 
        ADD CONSTRAINT reporting_effort_items_reporting_effort_id_fkey 
        FOREIGN KEY (reporting_effort_id) REFERENCES reporting_efforts(id) ON DELETE CASCADE
    """)
    
    # 3.2: Update reporting_effort_item_tracker.reporting_effort_item_id constraint
    print("  - Updating tracker.reporting_effort_item_id constraint...")
    op.execute("ALTER TABLE reporting_effort_item_tracker DROP CONSTRAINT reporting_effort_item_tracker_reporting_effort_item_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_item_tracker 
        ADD CONSTRAINT reporting_effort_item_tracker_reporting_effort_item_id_fkey 
        FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE
    """)
    
    # ========================================================================
    # PHASE 4: Package System Constraints
    # ========================================================================
    
    print("📋 Phase 4: Updating package system constraints...")
    
    # 4.1: Update package_items.package_id constraint
    print("  - Updating package_items.package_id constraint...")
    op.execute("ALTER TABLE package_items DROP CONSTRAINT package_items_package_id_fkey")
    op.execute("""
        ALTER TABLE package_items 
        ADD CONSTRAINT package_items_package_id_fkey 
        FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE
    """)
    
    # ========================================================================
    # PHASE 5: Detail Table Constraints
    # ========================================================================
    
    print("📋 Phase 5: Updating detail table constraints...")
    
    # 5.1: Package TLF Details
    print("  - Updating package_tlf_details.package_item_id constraint...")
    op.execute("ALTER TABLE package_tlf_details DROP CONSTRAINT package_tlf_details_package_item_id_fkey")
    op.execute("""
        ALTER TABLE package_tlf_details 
        ADD CONSTRAINT package_tlf_details_package_item_id_fkey 
        FOREIGN KEY (package_item_id) REFERENCES package_items(id) ON DELETE CASCADE
    """)
    
    # 5.2: Package Dataset Details
    print("  - Updating package_dataset_details.package_item_id constraint...")
    op.execute("ALTER TABLE package_dataset_details DROP CONSTRAINT package_dataset_details_package_item_id_fkey")
    op.execute("""
        ALTER TABLE package_dataset_details 
        ADD CONSTRAINT package_dataset_details_package_item_id_fkey 
        FOREIGN KEY (package_item_id) REFERENCES package_items(id) ON DELETE CASCADE
    """)
    
    # 5.3: Package Item Footnotes
    print("  - Updating package_item_footnotes.package_item_id constraint...")
    op.execute("ALTER TABLE package_item_footnotes DROP CONSTRAINT package_item_footnotes_package_item_id_fkey")
    op.execute("""
        ALTER TABLE package_item_footnotes 
        ADD CONSTRAINT package_item_footnotes_package_item_id_fkey 
        FOREIGN KEY (package_item_id) REFERENCES package_items(id) ON DELETE CASCADE
    """)
    
    # 5.4: Package Item Acronyms
    print("  - Updating package_item_acronyms.package_item_id constraint...")
    op.execute("ALTER TABLE package_item_acronyms DROP CONSTRAINT package_item_acronyms_package_item_id_fkey")
    op.execute("""
        ALTER TABLE package_item_acronyms 
        ADD CONSTRAINT package_item_acronyms_package_item_id_fkey 
        FOREIGN KEY (package_item_id) REFERENCES package_items(id) ON DELETE CASCADE
    """)
    
    # 5.5: Reporting Effort TLF Details
    print("  - Updating reporting_effort_tlf_details.reporting_effort_item_id constraint...")
    op.execute("ALTER TABLE reporting_effort_tlf_details DROP CONSTRAINT reporting_effort_tlf_details_reporting_effort_item_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_tlf_details 
        ADD CONSTRAINT reporting_effort_tlf_details_reporting_effort_item_id_fkey 
        FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE
    """)
    
    # 5.6: Reporting Effort Dataset Details
    print("  - Updating reporting_effort_dataset_details.reporting_effort_item_id constraint...")
    op.execute("ALTER TABLE reporting_effort_dataset_details DROP CONSTRAINT reporting_effort_dataset_details_reporting_effort_item_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_dataset_details 
        ADD CONSTRAINT reporting_effort_dataset_details_reporting_effort_item_id_fkey 
        FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE
    """)
    
    # 5.7: Reporting Effort Item Footnotes
    print("  - Updating reporting_effort_item_footnotes.reporting_effort_item_id constraint...")
    op.execute("ALTER TABLE reporting_effort_item_footnotes DROP CONSTRAINT reporting_effort_item_footnotes_reporting_effort_item_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_item_footnotes 
        ADD CONSTRAINT reporting_effort_item_footnotes_reporting_effort_item_id_fkey 
        FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE
    """)
    
    # 5.8: Reporting Effort Item Acronyms
    print("  - Updating reporting_effort_item_acronyms.reporting_effort_item_id constraint...")
    op.execute("ALTER TABLE reporting_effort_item_acronyms DROP CONSTRAINT reporting_effort_item_acronyms_reporting_effort_item_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_item_acronyms 
        ADD CONSTRAINT reporting_effort_item_acronyms_reporting_effort_item_id_fkey 
        FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id) ON DELETE CASCADE
    """)
    
    # ========================================================================
    # PHASE 6: User-Related Constraints (CAREFUL - preserve audit trails)
    # ========================================================================
    
    print("📋 Phase 6: Updating user-related constraints...")
    
    # 6.1: Audit Log - SET NULL to preserve audit history
    print("  - Updating audit_log.user_id constraint (SET NULL)...")
    op.execute("ALTER TABLE audit_log DROP CONSTRAINT audit_log_user_id_fkey")
    op.execute("""
        ALTER TABLE audit_log 
        ADD CONSTRAINT audit_log_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    """)
    
    # 6.2: Tracker Production Programmer - SET NULL (unassign when user deleted)
    print("  - Updating tracker.production_programmer_id constraint (SET NULL)...")
    op.execute("ALTER TABLE reporting_effort_item_tracker DROP CONSTRAINT reporting_effort_item_tracker_production_programmer_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_item_tracker 
        ADD CONSTRAINT reporting_effort_item_tracker_production_programmer_id_fkey 
        FOREIGN KEY (production_programmer_id) REFERENCES users(id) ON DELETE SET NULL
    """)
    
    # 6.3: Tracker QC Programmer - SET NULL (unassign when user deleted)
    print("  - Updating tracker.qc_programmer_id constraint (SET NULL)...")
    op.execute("ALTER TABLE reporting_effort_item_tracker DROP CONSTRAINT reporting_effort_item_tracker_qc_programmer_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_item_tracker 
        ADD CONSTRAINT reporting_effort_item_tracker_qc_programmer_id_fkey 
        FOREIGN KEY (qc_programmer_id) REFERENCES users(id) ON DELETE SET NULL
    """)
    
    # 6.4: Tracker Comments User - RESTRICT (prevent user deletion if they have comments)
    print("  - Updating tracker_comments.user_id constraint (RESTRICT)...")
    op.execute("ALTER TABLE tracker_comments DROP CONSTRAINT tracker_comments_user_id_fkey")
    op.execute("""
        ALTER TABLE tracker_comments 
        ADD CONSTRAINT tracker_comments_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
    """)
    
    # 6.5: Tracker Comments Resolved By - SET NULL (preserve comment if resolver deleted)
    print("  - Updating tracker_comments.resolved_by_user_id constraint (SET NULL)...")
    op.execute("ALTER TABLE tracker_comments DROP CONSTRAINT tracker_comments_resolved_by_user_id_fkey")
    op.execute("""
        ALTER TABLE tracker_comments 
        ADD CONSTRAINT tracker_comments_resolved_by_user_id_fkey 
        FOREIGN KEY (resolved_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    """)
    
    # ========================================================================
    # PHASE 7: Text Element References (SET NULL - preserve data)
    # ========================================================================
    
    print("📋 Phase 7: Updating text element references...")
    
    # 7.1: Package TLF Details - Title
    print("  - Updating package_tlf_details.title_id constraint (SET NULL)...")
    op.execute("ALTER TABLE package_tlf_details DROP CONSTRAINT package_tlf_details_title_id_fkey")
    op.execute("""
        ALTER TABLE package_tlf_details 
        ADD CONSTRAINT package_tlf_details_title_id_fkey 
        FOREIGN KEY (title_id) REFERENCES text_elements(id) ON DELETE SET NULL
    """)
    
    # 7.2: Package TLF Details - Population Flag
    print("  - Updating package_tlf_details.population_flag_id constraint (SET NULL)...")
    op.execute("ALTER TABLE package_tlf_details DROP CONSTRAINT package_tlf_details_population_flag_id_fkey")
    op.execute("""
        ALTER TABLE package_tlf_details 
        ADD CONSTRAINT package_tlf_details_population_flag_id_fkey 
        FOREIGN KEY (population_flag_id) REFERENCES text_elements(id) ON DELETE SET NULL
    """)
    
    # 7.3: Package TLF Details - ICH Category
    print("  - Updating package_tlf_details.ich_category_id constraint (SET NULL)...")
    op.execute("ALTER TABLE package_tlf_details DROP CONSTRAINT package_tlf_details_ich_category_id_fkey")
    op.execute("""
        ALTER TABLE package_tlf_details 
        ADD CONSTRAINT package_tlf_details_ich_category_id_fkey 
        FOREIGN KEY (ich_category_id) REFERENCES text_elements(id) ON DELETE SET NULL
    """)
    
    # Continue with similar updates for reporting effort TLF details...
    print("  - Updating reporting_effort_tlf_details text element constraints (SET NULL)...")
    
    # 7.4: Reporting Effort TLF Details - Title
    op.execute("ALTER TABLE reporting_effort_tlf_details DROP CONSTRAINT reporting_effort_tlf_details_title_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_tlf_details 
        ADD CONSTRAINT reporting_effort_tlf_details_title_id_fkey 
        FOREIGN KEY (title_id) REFERENCES text_elements(id) ON DELETE SET NULL
    """)
    
    # 7.5: Reporting Effort TLF Details - Population Flag
    op.execute("ALTER TABLE reporting_effort_tlf_details DROP CONSTRAINT reporting_effort_tlf_details_population_flag_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_tlf_details 
        ADD CONSTRAINT reporting_effort_tlf_details_population_flag_id_fkey 
        FOREIGN KEY (population_flag_id) REFERENCES text_elements(id) ON DELETE SET NULL
    """)
    
    # 7.6: Reporting Effort TLF Details - ICH Category
    op.execute("ALTER TABLE reporting_effort_tlf_details DROP CONSTRAINT reporting_effort_tlf_details_ich_category_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_tlf_details 
        ADD CONSTRAINT reporting_effort_tlf_details_ich_category_id_fkey 
        FOREIGN KEY (ich_category_id) REFERENCES text_elements(id) ON DELETE SET NULL
    """)
    
    # 7.7: Footnote and Acronym references - RESTRICT to preserve referential integrity
    print("  - Updating footnote and acronym references (RESTRICT)...")
    
    # Package Item Footnotes
    op.execute("ALTER TABLE package_item_footnotes DROP CONSTRAINT package_item_footnotes_footnote_id_fkey")
    op.execute("""
        ALTER TABLE package_item_footnotes 
        ADD CONSTRAINT package_item_footnotes_footnote_id_fkey 
        FOREIGN KEY (footnote_id) REFERENCES text_elements(id) ON DELETE RESTRICT
    """)
    
    # Package Item Acronyms
    op.execute("ALTER TABLE package_item_acronyms DROP CONSTRAINT package_item_acronyms_acronym_id_fkey")
    op.execute("""
        ALTER TABLE package_item_acronyms 
        ADD CONSTRAINT package_item_acronyms_acronym_id_fkey 
        FOREIGN KEY (acronym_id) REFERENCES text_elements(id) ON DELETE RESTRICT
    """)
    
    # Reporting Effort Item Footnotes
    op.execute("ALTER TABLE reporting_effort_item_footnotes DROP CONSTRAINT reporting_effort_item_footnotes_footnote_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_item_footnotes 
        ADD CONSTRAINT reporting_effort_item_footnotes_footnote_id_fkey 
        FOREIGN KEY (footnote_id) REFERENCES text_elements(id) ON DELETE RESTRICT
    """)
    
    # Reporting Effort Item Acronyms
    op.execute("ALTER TABLE reporting_effort_item_acronyms DROP CONSTRAINT reporting_effort_item_acronyms_acronym_id_fkey")
    op.execute("""
        ALTER TABLE reporting_effort_item_acronyms 
        ADD CONSTRAINT reporting_effort_item_acronyms_acronym_id_fkey 
        FOREIGN KEY (acronym_id) REFERENCES text_elements(id) ON DELETE RESTRICT
    """)
    
    print("✅ CASCADE DELETE constraints migration completed successfully!")
    print("🎉 Orphaned records issue is now resolved!")


def downgrade() -> None:
    """
    Rollback CASCADE DELETE constraints to original state.
    
    WARNING: This rollback removes the protection against orphaned records.
    Only use this if you need to revert the changes for debugging purposes.
    """
    
    print("⚠️  Rolling back CASCADE DELETE constraints...")
    print("   This will restore the original constraints WITHOUT CASCADE DELETE")
    print("   This means orphaned records can occur again!")
    
    # Rollback in reverse order of application
    
    # Phase 7: Text Element References
    print("📋 Rolling back text element references...")
    
    # Rollback acronym and footnote references
    op.execute("ALTER TABLE reporting_effort_item_acronyms DROP CONSTRAINT reporting_effort_item_acronyms_acronym_id_fkey")
    op.execute("ALTER TABLE reporting_effort_item_acronyms ADD CONSTRAINT reporting_effort_item_acronyms_acronym_id_fkey FOREIGN KEY (acronym_id) REFERENCES text_elements(id)")
    
    op.execute("ALTER TABLE reporting_effort_item_footnotes DROP CONSTRAINT reporting_effort_item_footnotes_footnote_id_fkey")
    op.execute("ALTER TABLE reporting_effort_item_footnotes ADD CONSTRAINT reporting_effort_item_footnotes_footnote_id_fkey FOREIGN KEY (footnote_id) REFERENCES text_elements(id)")
    
    op.execute("ALTER TABLE package_item_acronyms DROP CONSTRAINT package_item_acronyms_acronym_id_fkey")
    op.execute("ALTER TABLE package_item_acronyms ADD CONSTRAINT package_item_acronyms_acronym_id_fkey FOREIGN KEY (acronym_id) REFERENCES text_elements(id)")
    
    op.execute("ALTER TABLE package_item_footnotes DROP CONSTRAINT package_item_footnotes_footnote_id_fkey")
    op.execute("ALTER TABLE package_item_footnotes ADD CONSTRAINT package_item_footnotes_footnote_id_fkey FOREIGN KEY (footnote_id) REFERENCES text_elements(id)")
    
    # Rollback TLF detail text element references
    op.execute("ALTER TABLE reporting_effort_tlf_details DROP CONSTRAINT reporting_effort_tlf_details_ich_category_id_fkey")
    op.execute("ALTER TABLE reporting_effort_tlf_details ADD CONSTRAINT reporting_effort_tlf_details_ich_category_id_fkey FOREIGN KEY (ich_category_id) REFERENCES text_elements(id)")
    
    op.execute("ALTER TABLE reporting_effort_tlf_details DROP CONSTRAINT reporting_effort_tlf_details_population_flag_id_fkey")
    op.execute("ALTER TABLE reporting_effort_tlf_details ADD CONSTRAINT reporting_effort_tlf_details_population_flag_id_fkey FOREIGN KEY (population_flag_id) REFERENCES text_elements(id)")
    
    op.execute("ALTER TABLE reporting_effort_tlf_details DROP CONSTRAINT reporting_effort_tlf_details_title_id_fkey")
    op.execute("ALTER TABLE reporting_effort_tlf_details ADD CONSTRAINT reporting_effort_tlf_details_title_id_fkey FOREIGN KEY (title_id) REFERENCES text_elements(id)")
    
    op.execute("ALTER TABLE package_tlf_details DROP CONSTRAINT package_tlf_details_ich_category_id_fkey")
    op.execute("ALTER TABLE package_tlf_details ADD CONSTRAINT package_tlf_details_ich_category_id_fkey FOREIGN KEY (ich_category_id) REFERENCES text_elements(id)")
    
    op.execute("ALTER TABLE package_tlf_details DROP CONSTRAINT package_tlf_details_population_flag_id_fkey")
    op.execute("ALTER TABLE package_tlf_details ADD CONSTRAINT package_tlf_details_population_flag_id_fkey FOREIGN KEY (population_flag_id) REFERENCES text_elements(id)")
    
    op.execute("ALTER TABLE package_tlf_details DROP CONSTRAINT package_tlf_details_title_id_fkey")
    op.execute("ALTER TABLE package_tlf_details ADD CONSTRAINT package_tlf_details_title_id_fkey FOREIGN KEY (title_id) REFERENCES text_elements(id)")
    
    # Phase 6: User-Related Constraints
    print("📋 Rolling back user-related constraints...")
    
    op.execute("ALTER TABLE tracker_comments DROP CONSTRAINT tracker_comments_resolved_by_user_id_fkey")
    op.execute("ALTER TABLE tracker_comments ADD CONSTRAINT tracker_comments_resolved_by_user_id_fkey FOREIGN KEY (resolved_by_user_id) REFERENCES users(id)")
    
    op.execute("ALTER TABLE tracker_comments DROP CONSTRAINT tracker_comments_user_id_fkey")
    op.execute("ALTER TABLE tracker_comments ADD CONSTRAINT tracker_comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)")
    
    op.execute("ALTER TABLE reporting_effort_item_tracker DROP CONSTRAINT reporting_effort_item_tracker_qc_programmer_id_fkey")
    op.execute("ALTER TABLE reporting_effort_item_tracker ADD CONSTRAINT reporting_effort_item_tracker_qc_programmer_id_fkey FOREIGN KEY (qc_programmer_id) REFERENCES users(id)")
    
    op.execute("ALTER TABLE reporting_effort_item_tracker DROP CONSTRAINT reporting_effort_item_tracker_production_programmer_id_fkey")
    op.execute("ALTER TABLE reporting_effort_item_tracker ADD CONSTRAINT reporting_effort_item_tracker_production_programmer_id_fkey FOREIGN KEY (production_programmer_id) REFERENCES users(id)")
    
    op.execute("ALTER TABLE audit_log DROP CONSTRAINT audit_log_user_id_fkey")
    op.execute("ALTER TABLE audit_log ADD CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)")
    
    # Phase 5: Detail Table Constraints
    print("📋 Rolling back detail table constraints...")
    
    op.execute("ALTER TABLE reporting_effort_item_acronyms DROP CONSTRAINT reporting_effort_item_acronyms_reporting_effort_item_id_fkey")
    op.execute("ALTER TABLE reporting_effort_item_acronyms ADD CONSTRAINT reporting_effort_item_acronyms_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id)")
    
    op.execute("ALTER TABLE reporting_effort_item_footnotes DROP CONSTRAINT reporting_effort_item_footnotes_reporting_effort_item_id_fkey")
    op.execute("ALTER TABLE reporting_effort_item_footnotes ADD CONSTRAINT reporting_effort_item_footnotes_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id)")
    
    op.execute("ALTER TABLE reporting_effort_dataset_details DROP CONSTRAINT reporting_effort_dataset_details_reporting_effort_item_id_fkey")
    op.execute("ALTER TABLE reporting_effort_dataset_details ADD CONSTRAINT reporting_effort_dataset_details_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id)")
    
    op.execute("ALTER TABLE reporting_effort_tlf_details DROP CONSTRAINT reporting_effort_tlf_details_reporting_effort_item_id_fkey")
    op.execute("ALTER TABLE reporting_effort_tlf_details ADD CONSTRAINT reporting_effort_tlf_details_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id)")
    
    op.execute("ALTER TABLE package_item_acronyms DROP CONSTRAINT package_item_acronyms_package_item_id_fkey")
    op.execute("ALTER TABLE package_item_acronyms ADD CONSTRAINT package_item_acronyms_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES package_items(id)")
    
    op.execute("ALTER TABLE package_item_footnotes DROP CONSTRAINT package_item_footnotes_package_item_id_fkey")
    op.execute("ALTER TABLE package_item_footnotes ADD CONSTRAINT package_item_footnotes_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES package_items(id)")
    
    op.execute("ALTER TABLE package_dataset_details DROP CONSTRAINT package_dataset_details_package_item_id_fkey")
    op.execute("ALTER TABLE package_dataset_details ADD CONSTRAINT package_dataset_details_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES package_items(id)")
    
    op.execute("ALTER TABLE package_tlf_details DROP CONSTRAINT package_tlf_details_package_item_id_fkey")
    op.execute("ALTER TABLE package_tlf_details ADD CONSTRAINT package_tlf_details_package_item_id_fkey FOREIGN KEY (package_item_id) REFERENCES package_items(id)")
    
    # Phase 4: Package System Constraints
    print("📋 Rolling back package system constraints...")
    
    op.execute("ALTER TABLE package_items DROP CONSTRAINT package_items_package_id_fkey")
    op.execute("ALTER TABLE package_items ADD CONSTRAINT package_items_package_id_fkey FOREIGN KEY (package_id) REFERENCES packages(id)")
    
    # Phase 3: Reporting Effort Chain Constraints
    print("📋 Rolling back reporting effort chain constraints...")
    
    op.execute("ALTER TABLE reporting_effort_item_tracker DROP CONSTRAINT reporting_effort_item_tracker_reporting_effort_item_id_fkey")
    op.execute("ALTER TABLE reporting_effort_item_tracker ADD CONSTRAINT reporting_effort_item_tracker_reporting_effort_item_id_fkey FOREIGN KEY (reporting_effort_item_id) REFERENCES reporting_effort_items(id)")
    
    op.execute("ALTER TABLE reporting_effort_items DROP CONSTRAINT reporting_effort_items_reporting_effort_id_fkey")
    op.execute("ALTER TABLE reporting_effort_items ADD CONSTRAINT reporting_effort_items_reporting_effort_id_fkey FOREIGN KEY (reporting_effort_id) REFERENCES reporting_efforts(id)")
    
    # Phase 2: Database Release Constraints
    print("📋 Rolling back database release constraints...")
    
    op.execute("ALTER TABLE reporting_efforts DROP CONSTRAINT reporting_efforts_database_release_id_fkey")
    op.execute("ALTER TABLE reporting_efforts ADD CONSTRAINT reporting_efforts_database_release_id_fkey FOREIGN KEY (database_release_id) REFERENCES database_releases(id)")
    
    # Phase 1: Study-Related Constraints
    print("📋 Rolling back study-related constraints...")
    
    op.execute("ALTER TABLE reporting_efforts DROP CONSTRAINT reporting_efforts_study_id_fkey")
    op.execute("ALTER TABLE reporting_efforts ADD CONSTRAINT reporting_efforts_study_id_fkey FOREIGN KEY (study_id) REFERENCES studies(id)")
    
    op.execute("ALTER TABLE database_releases DROP CONSTRAINT database_releases_study_id_fkey")
    op.execute("ALTER TABLE database_releases ADD CONSTRAINT database_releases_study_id_fkey FOREIGN KEY (study_id) REFERENCES studies(id)")
    
    print("⚠️  Rollback completed!")
    print("🚨 WARNING: The database is now vulnerable to orphaned records again!")
    print("   Consider running the upgrade again after fixing any issues.")
