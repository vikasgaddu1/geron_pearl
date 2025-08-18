#!/usr/bin/env python
"""
Find and analyze duplicate studies in the database.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append('.')

from app.db.session import AsyncSessionLocal

async def find_duplicate_studies():
    """Find duplicate studies and analyze their impact."""
    
    async with AsyncSessionLocal() as db:
        print("🔍 Finding Duplicate Studies")
        print("=" * 50)
        
        # Find studies with duplicate names
        print("\n📊 Finding duplicate study labels...")
        result = await db.execute(text("""
            SELECT 
                study_label,
                COUNT(*) as count,
                ARRAY_AGG(id ORDER BY id) as study_ids,
                ARRAY_AGG(created_at ORDER BY id) as created_dates
            FROM studies 
            GROUP BY study_label 
            HAVING COUNT(*) > 1
            ORDER BY study_label
        """))
        duplicates = result.fetchall()
        
        if not duplicates:
            print("   ✅ No duplicate studies found")
            return
        
        print(f"   🚨 Found {len(duplicates)} duplicate study names:")
        
        for duplicate in duplicates:
            study_label, count, study_ids, created_dates = duplicate
            print(f"\n   📋 Study: '{study_label}' ({count} duplicates)")
            print(f"      IDs: {study_ids}")
            
            # Check what's linked to each duplicate
            for study_id in study_ids:
                print(f"\n      🔍 Study ID {study_id}:")
                
                # Check database releases
                result = await db.execute(text("""
                    SELECT COUNT(*) FROM database_releases WHERE study_id = :id
                """), {"id": study_id})
                db_releases_count = result.scalar()
                
                # Check reporting efforts  
                result = await db.execute(text("""
                    SELECT COUNT(*) FROM reporting_efforts WHERE study_id = :id
                """), {"id": study_id})
                efforts_count = result.scalar()
                
                # Check total items through reporting efforts
                result = await db.execute(text("""
                    SELECT COUNT(rei.id) 
                    FROM reporting_effort_items rei
                    JOIN reporting_efforts re ON rei.reporting_effort_id = re.id
                    WHERE re.study_id = :id
                """), {"id": study_id})
                items_count = result.scalar()
                
                # Check trackers
                result = await db.execute(text("""
                    SELECT COUNT(t.id)
                    FROM reporting_effort_item_tracker t
                    JOIN reporting_effort_items rei ON t.reporting_effort_item_id = rei.id  
                    JOIN reporting_efforts re ON rei.reporting_effort_id = re.id
                    WHERE re.study_id = :id
                """), {"id": study_id})
                trackers_count = result.scalar()
                
                print(f"         - Database Releases: {db_releases_count}")
                print(f"         - Reporting Efforts: {efforts_count}")  
                print(f"         - Items: {items_count}")
                print(f"         - Trackers: {trackers_count}")
                
                # Determine if this study can be safely deleted
                total_data = db_releases_count + efforts_count + items_count + trackers_count
                if total_data == 0:
                    print(f"         ✅ SAFE TO DELETE (no linked data)")
                else:
                    print(f"         ⚠️  HAS DATA (deletion will cascade)")
        
        print(f"\n" + "=" * 50)
        print(f"💡 RECOMMENDATION:")
        print(f"   1. Keep the OLDEST study (lowest ID) for each duplicate name")
        print(f"   2. If needed, merge data from other studies into the keeper")  
        print(f"   3. Delete the duplicate studies (CASCADE will handle linked data)")
        print(f"   4. Or rename studies if they're actually different")

if __name__ == "__main__":
    asyncio.run(find_duplicate_studies())
