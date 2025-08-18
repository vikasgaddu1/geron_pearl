#!/usr/bin/env python
"""
Clean up duplicate PEARL-2025-001 studies by keeping Study ID 35 (has most data).
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append('.')

from app.db.session import AsyncSessionLocal

async def clean_duplicate_studies():
    """Clean up duplicate PEARL-2025-001 studies."""
    
    async with AsyncSessionLocal() as db:
        print("🧹 Cleaning Up Duplicate PEARL-2025-001 Studies")
        print("=" * 60)
        
        # Show current state
        print("\n📊 Current State:")
        result = await db.execute(text("""
            SELECT 
                s.id, 
                s.study_label,
                COUNT(DISTINCT dr.id) as db_releases,
                COUNT(DISTINCT re.id) as reporting_efforts,
                COUNT(DISTINCT rei.id) as items
            FROM studies s
            LEFT JOIN database_releases dr ON s.id = dr.study_id
            LEFT JOIN reporting_efforts re ON s.id = re.study_id  
            LEFT JOIN reporting_effort_items rei ON re.id = rei.reporting_effort_id
            WHERE s.study_label = 'PEARL-2025-001'
            GROUP BY s.id, s.study_label
            ORDER BY s.id
        """))
        studies = result.fetchall()
        
        for study in studies:
            study_id, label, db_releases, efforts, items = study
            print(f"   Study ID {study_id}: {db_releases} releases, {efforts} efforts, {items} items")
        
        print(f"\n🎯 PLAN:")
        print(f"   ✅ KEEP: Study ID 35 (has most data: 8 items)")
        print(f"   ❌ DELETE: Study IDs 32, 33, 34 (will CASCADE delete their data)")
        
        # Confirm before proceeding
        print(f"\n⚠️  This will permanently delete:")
        for study_id in [32, 33, 34]:
            result = await db.execute(text("""
                SELECT 
                    COUNT(DISTINCT dr.id) as db_releases,
                    COUNT(DISTINCT re.id) as reporting_efforts,
                    COUNT(DISTINCT rei.id) as items,
                    COUNT(DISTINCT t.id) as trackers
                FROM studies s
                LEFT JOIN database_releases dr ON s.id = dr.study_id
                LEFT JOIN reporting_efforts re ON s.id = re.study_id  
                LEFT JOIN reporting_effort_items rei ON re.id = rei.reporting_effort_id
                LEFT JOIN reporting_effort_item_tracker t ON rei.id = t.reporting_effort_item_id
                WHERE s.id = :id
                GROUP BY s.id
            """), {"id": study_id})
            data = result.fetchone()
            if data:
                db_releases, efforts, items, trackers = data
                print(f"   Study ID {study_id}: {db_releases} releases, {efforts} efforts, {items} items, {trackers} trackers")
        
        # Ask for confirmation
        response = input(f"\n🤔 Proceed with cleanup? Type 'YES' to continue, anything else to cancel: ")
        
        if response != "YES":
            print("❌ Cleanup cancelled by user")
            return False
        
        print(f"\n🗑️  Deleting duplicate studies...")
        
        # Delete duplicate studies (CASCADE will handle all related data)
        for study_id in [32, 33, 34]:
            print(f"   Deleting Study ID {study_id}...")
            result = await db.execute(text("DELETE FROM studies WHERE id = :id"), {"id": study_id})
            await db.commit()
            print(f"   ✅ Study ID {study_id} deleted (CASCADE cleaned up all related data)")
        
        print(f"\n🎉 Cleanup completed!")
        
        # Verify final state
        print(f"\n📊 Final State:")
        result = await db.execute(text("""
            SELECT id, study_label FROM studies WHERE study_label = 'PEARL-2025-001'
        """))
        remaining = result.fetchall()
        
        if len(remaining) == 1:
            study_id, label = remaining[0]
            print(f"   ✅ Only one 'PEARL-2025-001' study remains: ID {study_id}")
            
            # Count its data
            result = await db.execute(text("""
                SELECT 
                    COUNT(DISTINCT dr.id) as db_releases,
                    COUNT(DISTINCT re.id) as reporting_efforts,
                    COUNT(DISTINCT rei.id) as items
                FROM studies s
                LEFT JOIN database_releases dr ON s.id = dr.study_id
                LEFT JOIN reporting_efforts re ON s.id = re.study_id  
                LEFT JOIN reporting_effort_items rei ON re.id = rei.reporting_effort_id
                WHERE s.id = :id
                GROUP BY s.id
            """), {"id": study_id})
            data = result.fetchone()
            if data:
                db_releases, efforts, items = data
                print(f"      Data: {db_releases} releases, {efforts} efforts, {items} items")
        else:
            print(f"   ❌ ERROR: Found {len(remaining)} studies, expected 1")
            return False
        
        print(f"\n✅ SUCCESS: Duplicate studies cleaned up!")
        print(f"   Your tracker dropdown should now show only one 'PEARL-2025-001' entry")
        return True

if __name__ == "__main__":
    success = asyncio.run(clean_duplicate_studies())
    sys.exit(0 if success else 1)
