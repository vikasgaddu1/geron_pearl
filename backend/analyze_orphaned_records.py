#!/usr/bin/env python
"""
Analyze database for orphaned records that will prevent CASCADE constraint addition.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append('.')

from app.db.session import AsyncSessionLocal

async def analyze_orphaned_records():
    """Analyze the database for orphaned records."""
    
    async with AsyncSessionLocal() as db:
        print("🔍 PEARL Database Orphaned Records Analysis")
        print("=" * 50)
        
        # Check orphaned reporting_efforts (missing studies)
        print("\n1. Orphaned Reporting Efforts (missing studies):")
        result = await db.execute(text("""
            SELECT re.id, re.study_id, re.database_release_label
            FROM reporting_efforts re
            LEFT JOIN studies s ON re.study_id = s.id
            WHERE s.id IS NULL
            ORDER BY re.id;
        """))
        orphaned_reporting_efforts = result.fetchall()
        
        if orphaned_reporting_efforts:
            print(f"   ❌ Found {len(orphaned_reporting_efforts)} orphaned reporting efforts:")
            for row in orphaned_reporting_efforts[:5]:  # Show first 5
                print(f"      - RE ID: {row[0]}, Missing Study ID: {row[1]}, Label: {row[2]}")
            if len(orphaned_reporting_efforts) > 5:
                print(f"      ... and {len(orphaned_reporting_efforts) - 5} more")
        else:
            print("   ✅ No orphaned reporting efforts found")
            
        # Check orphaned database_releases (missing studies)
        print("\n2. Orphaned Database Releases (missing studies):")
        result = await db.execute(text("""
            SELECT dr.id, dr.study_id, dr.database_release_label
            FROM database_releases dr
            LEFT JOIN studies s ON dr.study_id = s.id
            WHERE s.id IS NULL
            ORDER BY dr.id;
        """))
        orphaned_db_releases = result.fetchall()
        
        if orphaned_db_releases:
            print(f"   ❌ Found {len(orphaned_db_releases)} orphaned database releases:")
            for row in orphaned_db_releases[:5]:
                print(f"      - DR ID: {row[0]}, Missing Study ID: {row[1]}, Label: {row[2]}")
            if len(orphaned_db_releases) > 5:
                print(f"      ... and {len(orphaned_db_releases) - 5} more")
        else:
            print("   ✅ No orphaned database releases found")
            
        # Check orphaned reporting_efforts (missing database_releases)
        print("\n3. Orphaned Reporting Efforts (missing database releases):")
        result = await db.execute(text("""
            SELECT re.id, re.database_release_id, re.database_release_label
            FROM reporting_efforts re
            LEFT JOIN database_releases dr ON re.database_release_id = dr.id
            WHERE dr.id IS NULL
            ORDER BY re.id;
        """))
        orphaned_re_by_dr = result.fetchall()
        
        if orphaned_re_by_dr:
            print(f"   ❌ Found {len(orphaned_re_by_dr)} reporting efforts with missing database releases:")
            for row in orphaned_re_by_dr[:5]:
                print(f"      - RE ID: {row[0]}, Missing DB Release ID: {row[1]}, Label: {row[2]}")
            if len(orphaned_re_by_dr) > 5:
                print(f"      ... and {len(orphaned_re_by_dr) - 5} more")
        else:
            print("   ✅ No reporting efforts with missing database releases")
            
        # Check orphaned package_items (missing packages)
        print("\n4. Orphaned Package Items (missing packages):")
        result = await db.execute(text("""
            SELECT pi.id, pi.package_id, pi.item_code
            FROM package_items pi
            LEFT JOIN packages p ON pi.package_id = p.id
            WHERE p.id IS NULL
            ORDER BY pi.id;
        """))
        orphaned_package_items = result.fetchall()
        
        if orphaned_package_items:
            print(f"   ❌ Found {len(orphaned_package_items)} orphaned package items:")
            for row in orphaned_package_items[:5]:
                print(f"      - Item ID: {row[0]}, Missing Package ID: {row[1]}, Code: {row[2]}")
            if len(orphaned_package_items) > 5:
                print(f"      ... and {len(orphaned_package_items) - 5} more")
        else:
            print("   ✅ No orphaned package items found")
            
        # Check orphaned reporting_effort_items (missing reporting_efforts)
        print("\n5. Orphaned Reporting Effort Items (missing reporting efforts):")
        result = await db.execute(text("""
            SELECT rei.id, rei.reporting_effort_id, rei.item_code
            FROM reporting_effort_items rei
            LEFT JOIN reporting_efforts re ON rei.reporting_effort_id = re.id
            WHERE re.id IS NULL
            ORDER BY rei.id;
        """))
        orphaned_re_items = result.fetchall()
        
        if orphaned_re_items:
            print(f"   ❌ Found {len(orphaned_re_items)} orphaned reporting effort items:")
            for row in orphaned_re_items[:5]:
                print(f"      - Item ID: {row[0]}, Missing RE ID: {row[1]}, Code: {row[2]}")
            if len(orphaned_re_items) > 5:
                print(f"      ... and {len(orphaned_re_items) - 5} more")
        else:
            print("   ✅ No orphaned reporting effort items found")
            
        # Check orphaned trackers (missing items)
        print("\n6. Orphaned Trackers (missing reporting effort items):")
        result = await db.execute(text("""
            SELECT t.id, t.reporting_effort_item_id, t.production_status
            FROM reporting_effort_item_tracker t
            LEFT JOIN reporting_effort_items rei ON t.reporting_effort_item_id = rei.id
            WHERE rei.id IS NULL
            ORDER BY t.id;
        """))
        orphaned_trackers = result.fetchall()
        
        if orphaned_trackers:
            print(f"   ❌ Found {len(orphaned_trackers)} orphaned trackers:")
            for row in orphaned_trackers[:5]:
                print(f"      - Tracker ID: {row[0]}, Missing Item ID: {row[1]}, Status: {row[2]}")
            if len(orphaned_trackers) > 5:
                print(f"      ... and {len(orphaned_trackers) - 5} more")
        else:
            print("   ✅ No orphaned trackers found")
            
        # Check orphaned user assignments (missing users)
        print("\n7. Orphaned User Assignments (missing users):")
        result = await db.execute(text("""
            SELECT 
                t.id,
                t.production_programmer_id,
                t.qc_programmer_id,
                CASE 
                    WHEN u1.id IS NULL AND t.production_programmer_id IS NOT NULL THEN 'MISSING_PROD_USER'
                    WHEN u2.id IS NULL AND t.qc_programmer_id IS NOT NULL THEN 'MISSING_QC_USER'
                    ELSE 'OK'
                END as status
            FROM reporting_effort_item_tracker t
            LEFT JOIN users u1 ON t.production_programmer_id = u1.id
            LEFT JOIN users u2 ON t.qc_programmer_id = u2.id
            WHERE (t.production_programmer_id IS NOT NULL AND u1.id IS NULL)
               OR (t.qc_programmer_id IS NOT NULL AND u2.id IS NULL)
            ORDER BY t.id;
        """))
        orphaned_user_assignments = result.fetchall()
        
        if orphaned_user_assignments:
            print(f"   ❌ Found {len(orphaned_user_assignments)} trackers with missing user assignments:")
            for row in orphaned_user_assignments[:5]:
                print(f"      - Tracker ID: {row[0]}, Status: {row[3]}")
            if len(orphaned_user_assignments) > 5:
                print(f"      ... and {len(orphaned_user_assignments) - 5} more")
        else:
            print("   ✅ No trackers with missing user assignments")
            
        # Summary
        print("\n" + "=" * 50)
        total_orphans = (len(orphaned_reporting_efforts) + len(orphaned_db_releases) + 
                        len(orphaned_re_by_dr) + len(orphaned_package_items) + 
                        len(orphaned_re_items) + len(orphaned_trackers) + 
                        len(orphaned_user_assignments))
        
        if total_orphans > 0:
            print(f"🚨 TOTAL ORPHANED RECORDS: {total_orphans}")
            print("⚠️  These orphaned records MUST be cleaned up before adding CASCADE constraints!")
            print("\nNext steps:")
            print("1. Create cleanup scripts for each type of orphaned record")
            print("2. Decide on cleanup strategy (delete orphans or create missing parents)")
            print("3. Run cleanup in staging environment first")
            print("4. Only then proceed with CASCADE constraint migration")
        else:
            print("✅ NO ORPHANED RECORDS FOUND - Safe to proceed with CASCADE constraints!")
            
        return total_orphans

if __name__ == "__main__":
    total_orphans = asyncio.run(analyze_orphaned_records())
    sys.exit(1 if total_orphans > 0 else 0)
