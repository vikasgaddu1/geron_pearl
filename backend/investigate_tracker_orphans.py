#!/usr/bin/env python
"""
Investigate why tracker still shows orphaned studies.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append('.')

from app.db.session import AsyncSessionLocal

async def investigate_tracker_issue():
    """Investigate the tracker orphan issue."""
    
    async with AsyncSessionLocal() as db:
        print("🔍 Investigating Tracker Orphan Issue")
        print("=" * 50)
        
        # Check actual studies in database
        print("\n📊 Current Studies in Database:")
        result = await db.execute(text("SELECT id, study_label FROM studies ORDER BY id"))
        studies = result.fetchall()
        
        study_ids = set()
        for study in studies:
            print(f"   ID {study[0]}: {study[1]}")
            study_ids.add(study[0])
        
        if not studies:
            print("   ❌ No studies found!")
        
        # Check what reporting efforts exist and their study references
        print(f"\n📊 Reporting Efforts and their Study References:")
        result = await db.execute(text("""
            SELECT re.id, re.study_id, re.database_release_label, s.study_label
            FROM reporting_efforts re
            LEFT JOIN studies s ON re.study_id = s.id
            ORDER BY re.study_id, re.id
        """))
        efforts = result.fetchall()
        
        missing_study_ids = set()
        for effort in efforts:
            effort_id, study_id, release_label, study_label = effort
            if study_label is None:
                print(f"   ❌ ORPHANED: Effort ID {effort_id} references missing Study ID {study_id} - {release_label}")
                missing_study_ids.add(study_id)
            else:
                print(f"   ✅ OK: Effort ID {effort_id} → Study ID {study_id} ({study_label}) - {release_label}")
        
        # Check the specific study IDs mentioned in the UI (32, 33, 34, 35)
        print(f"\n🎯 Checking Specific Study IDs from UI (32, 33, 34, 35):")
        for study_id in [32, 33, 34, 35]:
            # Check if study exists
            result = await db.execute(text("SELECT study_label FROM studies WHERE id = :id"), {"id": study_id})
            study = result.fetchone()
            
            if study:
                print(f"   ✅ Study ID {study_id} EXISTS: {study[0]}")
            else:
                print(f"   ❌ Study ID {study_id} MISSING")
                
                # Check if any reporting efforts reference this missing study
                result = await db.execute(text("""
                    SELECT re.id, re.database_release_label
                    FROM reporting_efforts re 
                    WHERE re.study_id = :study_id
                """), {"study_id": study_id})
                orphaned_efforts = result.fetchall()
                
                for effort in orphaned_efforts:
                    print(f"      → Orphaned Reporting Effort ID {effort[0]}: {effort[1]}")
        
        # Check what the frontend query might be seeing
        print(f"\n🔍 Frontend Reporting Effort Query (what tracker dropdown shows):")
        result = await db.execute(text("""
            SELECT 
                re.id as effort_id,
                re.database_release_label,
                re.study_id,
                s.study_label,
                CASE 
                    WHEN s.study_label IS NULL THEN CONCAT('Study ', re.study_id)
                    ELSE s.study_label 
                END as display_label
            FROM reporting_efforts re
            LEFT JOIN studies s ON re.study_id = s.id
            ORDER BY re.study_id, re.id
        """))
        frontend_data = result.fetchall()
        
        for row in frontend_data:
            effort_id, release_label, study_id, study_label, display_label = row
            status = "✅ OK" if study_label else "❌ ORPHANED"
            print(f"   {status}: {release_label} ({display_label})")
        
        print(f"\n" + "=" * 50)
        if missing_study_ids:
            print(f"🚨 FOUND ORPHANED REPORTING EFFORTS!")
            print(f"   Missing Study IDs: {sorted(missing_study_ids)}")
            print(f"   This means our CASCADE DELETE constraints are not working as expected!")
            return False
        else:
            print(f"✅ No orphaned data found at database level")
            print(f"   The issue might be frontend caching or a different query")
            return True

if __name__ == "__main__":
    is_clean = asyncio.run(investigate_tracker_issue())
    sys.exit(0 if is_clean else 1)
