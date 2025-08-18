#!/usr/bin/env python
"""
Test CASCADE DELETE behavior after migration.

This script creates test data and verifies that CASCADE DELETE
constraints work correctly for all relationships.
"""

import asyncio
import sys
from datetime import datetime, date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append('.')

from app.db.session import AsyncSessionLocal
from app.crud import study, database_release, reporting_effort, reporting_effort_item, package
from app.schemas.study import StudyCreate  
from app.schemas.database_release import DatabaseReleaseCreate
from app.schemas.reporting_effort import ReportingEffortCreate
from app.schemas.reporting_effort_item import ReportingEffortItemCreate
from app.schemas.package import PackageCreate
from app.schemas.package_item import PackageItemCreate

async def test_cascade_deletion():
    """Test CASCADE DELETE behavior comprehensively."""
    
    print("🧪 CASCADE DELETE Behavior Testing")
    print("=" * 50)
    
    async with AsyncSessionLocal() as db:
        
        # ====================================================================
        # SETUP: Create test data hierarchy
        # ====================================================================
        
        print("\n📋 Phase 1: Creating test data hierarchy...")
        
        # Create test study
        study_data = StudyCreate(
            study_label=f"CASCADE_TEST_{int(datetime.now().timestamp())}"
        )
        test_study = await study.create(db, obj_in=study_data)
        print(f"   ✅ Created test study: ID {test_study.id}")
        
        # Create test database release
        db_release_data = DatabaseReleaseCreate(
            study_id=test_study.id,
            database_release_label="Test CASCADE DB Release",
            database_release_date=date.today()
        )
        test_db_release = await database_release.create(db, obj_in=db_release_data)
        print(f"   ✅ Created database release: ID {test_db_release.id}")
        
        # Create test reporting effort
        effort_data = ReportingEffortCreate(
            database_release_id=test_db_release.id,
            study_id=test_study.id,
            database_release_label="Test CASCADE Reporting Effort"
        )
        test_effort = await reporting_effort.create(db, obj_in=effort_data)
        print(f"   ✅ Created reporting effort: ID {test_effort.id}")
        
        # Create test reporting effort items
        item_data = ReportingEffortItemCreate(
            reporting_effort_id=test_effort.id,
            item_type="TLF",
            item_subtype="Table", 
            item_code="T_CASCADE_TEST",
            source_type="custom"
        )
        test_item = await reporting_effort_item.create(db, obj_in=item_data)
        print(f"   ✅ Created reporting effort item: ID {test_item.id}")
        
        # Create test package
        package_data = PackageCreate(package_name="CASCADE_TEST_PACKAGE")
        test_package = await package.create(db, obj_in=package_data)
        print(f"   ✅ Created test package: ID {test_package.id}")
        
        # ====================================================================
        # TEST 1: Count records before deletion
        # ====================================================================
        
        print("\n📋 Phase 2: Counting records before deletion...")
        
        # Count related records
        counts_before = {}
        
        # Study-related counts
        result = await db.execute(text("SELECT COUNT(*) FROM database_releases WHERE study_id = :study_id"), {"study_id": test_study.id})
        counts_before['database_releases'] = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM reporting_efforts WHERE study_id = :study_id"), {"study_id": test_study.id})
        counts_before['reporting_efforts'] = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM reporting_effort_items WHERE reporting_effort_id = :effort_id"), {"effort_id": test_effort.id})
        counts_before['reporting_effort_items'] = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM reporting_effort_item_tracker WHERE reporting_effort_item_id = :item_id"), {"item_id": test_item.id})
        counts_before['trackers'] = result.scalar()
        
        print(f"   📊 Before deletion counts:")
        print(f"      - Database releases: {counts_before['database_releases']}")
        print(f"      - Reporting efforts: {counts_before['reporting_efforts']}")
        print(f"      - Reporting effort items: {counts_before['reporting_effort_items']}")
        print(f"      - Trackers: {counts_before['trackers']}")
        
        # ====================================================================
        # TEST 2: Test CASCADE DELETE by deleting study
        # ====================================================================
        
        print("\n📋 Phase 3: Testing CASCADE DELETE by deleting study...")
        
        # Delete the study - this should cascade to all related records
        await db.execute(text("DELETE FROM studies WHERE id = :study_id"), {"study_id": test_study.id})
        await db.commit()
        print(f"   🗑️  Deleted study ID {test_study.id}")
        
        # ====================================================================
        # TEST 3: Verify CASCADE DELETE worked
        # ====================================================================
        
        print("\n📋 Phase 4: Verifying CASCADE DELETE worked...")
        
        # Count related records after deletion
        counts_after = {}
        
        result = await db.execute(text("SELECT COUNT(*) FROM database_releases WHERE study_id = :study_id"), {"study_id": test_study.id})
        counts_after['database_releases'] = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM reporting_efforts WHERE study_id = :study_id"), {"study_id": test_study.id})
        counts_after['reporting_efforts'] = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM reporting_effort_items WHERE reporting_effort_id = :effort_id"), {"effort_id": test_effort.id})
        counts_after['reporting_effort_items'] = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM reporting_effort_item_tracker WHERE reporting_effort_item_id = :item_id"), {"item_id": test_item.id})
        counts_after['trackers'] = result.scalar()
        
        print(f"   📊 After deletion counts:")
        print(f"      - Database releases: {counts_after['database_releases']}")
        print(f"      - Reporting efforts: {counts_after['reporting_efforts']}")
        print(f"      - Reporting effort items: {counts_after['reporting_effort_items']}")
        print(f"      - Trackers: {counts_after['trackers']}")
        
        # ====================================================================
        # TEST 4: Verify results
        # ====================================================================
        
        print("\n📋 Phase 5: Test Results Analysis...")
        
        all_tests_passed = True
        
        # Check that all related records were deleted
        expected_zero_counts = ['database_releases', 'reporting_efforts', 'reporting_effort_items', 'trackers']
        
        for table_name in expected_zero_counts:
            if counts_after[table_name] == 0:
                print(f"   ✅ {table_name}: Correctly deleted (0 records)")
            else:
                print(f"   ❌ {table_name}: CASCADE DELETE FAILED ({counts_after[table_name]} records remain)")
                all_tests_passed = False
        
        # ====================================================================
        # TEST 5: Test Package CASCADE DELETE
        # ====================================================================
        
        print("\n📋 Phase 6: Testing Package CASCADE DELETE...")
        
        # Create package item first
        from app.crud.package_item import package_item
        package_item_data = PackageItemCreate(
            package_id=test_package.id,
            item_type="TLF",
            item_subtype="Table",
            item_code="P_CASCADE_TEST"
        )
        test_package_item = await package_item.create(db, obj_in=package_item_data)
        print(f"   ✅ Created package item: ID {test_package_item.id}")
        
        # Count package items before deletion
        result = await db.execute(text("SELECT COUNT(*) FROM package_items WHERE package_id = :package_id"), {"package_id": test_package.id})
        package_items_before = result.scalar()
        print(f"   📊 Package items before deletion: {package_items_before}")
        
        # Delete package
        await db.execute(text("DELETE FROM packages WHERE id = :package_id"), {"package_id": test_package.id})
        await db.commit()
        print(f"   🗑️  Deleted package ID {test_package.id}")
        
        # Count package items after deletion
        result = await db.execute(text("SELECT COUNT(*) FROM package_items WHERE package_id = :package_id"), {"package_id": test_package.id})
        package_items_after = result.scalar()
        print(f"   📊 Package items after deletion: {package_items_after}")
        
        if package_items_after == 0:
            print(f"   ✅ Package CASCADE DELETE: SUCCESS")
        else:
            print(f"   ❌ Package CASCADE DELETE: FAILED ({package_items_after} items remain)")
            all_tests_passed = False
        
        # ====================================================================
        # FINAL RESULTS
        # ====================================================================
        
        print("\n" + "=" * 50)
        if all_tests_passed:
            print("🎉 ALL CASCADE DELETE TESTS PASSED!")
            print("✅ The migration was successful!")
            print("✅ Orphaned records will no longer occur!")
        else:
            print("❌ SOME CASCADE DELETE TESTS FAILED!")
            print("🚨 The migration may have issues!")
            print("⚠️  Please review the failed tests above.")
        
        return all_tests_passed

if __name__ == "__main__":
    test_passed = asyncio.run(test_cascade_deletion())
    sys.exit(0 if test_passed else 1)
