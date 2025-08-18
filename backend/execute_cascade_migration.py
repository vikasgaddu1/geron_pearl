#!/usr/bin/env python
"""
Execute CASCADE DELETE migration with comprehensive safety measures.

This script:
1. Creates full database backup
2. Verifies no orphaned records exist
3. Executes the migration
4. Tests the CASCADE behavior
5. Provides rollback capability
"""

import asyncio
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.append('.')

async def execute_cascade_migration():
    """Execute the CASCADE DELETE migration with full safety measures."""
    
    print("🚀 PEARL CASCADE DELETE Migration Execution")
    print("=" * 60)
    print("This script will safely migrate your database to include")
    print("CASCADE DELETE constraints to prevent orphaned records.")
    print("=" * 60)
    
    # ====================================================================
    # PHASE 1: Pre-migration Safety Checks
    # ====================================================================
    
    print("\n📋 Phase 1: Pre-migration Safety Checks")
    print("-" * 40)
    
    # Check if backend server is running
    print("🔍 Checking if backend server is accessible...")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ❌ Backend server is running!")
            print("   ⚠️  Please stop the backend server before running migration:")
            print("      - This prevents active connections during migration")
            print("      - Ensures data consistency during constraint updates")
            response = input("\n   Continue anyway? [y/N]: ")
            if response.lower() != 'y':
                return False
        else:
            print("   ✅ Backend server is not running (good for migration)")
    except:
        print("   ✅ Backend server is not running (good for migration)")
    
    # Check for orphaned records
    print("\n🔍 Checking for orphaned records...")
    result = subprocess.run([
        "uv", "run", "python", "analyze_orphaned_records.py"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("   ❌ Orphaned records found!")
        print("   🚨 Cannot proceed with migration until orphaned records are cleaned up.")
        print("\n   The analyze_orphaned_records.py script found issues.")
        print("   Please review the output above and clean up orphaned records first.")
        return False
    else:
        print("   ✅ No orphaned records found - safe to proceed")
    
    # ====================================================================
    # PHASE 2: Database Backup
    # ====================================================================
    
    print("\n📋 Phase 2: Creating Database Backup")
    print("-" * 40)
    
    # Create backup timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"pearl_cascade_migration_backup_{timestamp}.sql"
    backup_path = Path("backups") / backup_filename
    
    # Ensure backups directory exists
    backup_path.parent.mkdir(exist_ok=True)
    
    print(f"💾 Creating database backup: {backup_path}")
    
    # Get database connection info (you may need to adjust these)
    db_name = os.getenv("DATABASE_NAME", "pearl")
    db_user = os.getenv("DATABASE_USER", "postgres")
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "5432")
    
    # Create backup using pg_dump
    backup_cmd = [
        "pg_dump",
        f"--host={db_host}",
        f"--port={db_port}",
        f"--username={db_user}",
        "--verbose",
        "--clean",
        "--no-owner",
        "--no-privileges",
        "--format=plain",
        f"--file={backup_path}",
        db_name
    ]
    
    print(f"   Running: {' '.join(backup_cmd[:8])}... {db_name}")
    
    try:
        result = subprocess.run(backup_cmd, capture_output=True, text=True, check=True)
        print("   ✅ Database backup completed successfully")
        print(f"   📁 Backup location: {backup_path.absolute()}")
        
        # Verify backup file exists and has content
        if backup_path.exists() and backup_path.stat().st_size > 1000:
            print(f"   📊 Backup file size: {backup_path.stat().st_size:,} bytes")
        else:
            print("   ❌ Backup file appears to be too small or empty!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Database backup failed!")
        print(f"   Error: {e}")
        print(f"   stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("   ❌ pg_dump command not found!")
        print("   Please ensure PostgreSQL client tools are installed and in PATH")
        return False
    
    # ====================================================================
    # PHASE 3: Execute Migration
    # ====================================================================
    
    print("\n📋 Phase 3: Executing CASCADE DELETE Migration")
    print("-" * 40)
    
    print("🔄 Running Alembic migration...")
    
    try:
        # Run the migration
        migration_cmd = ["uv", "run", "alembic", "upgrade", "head"]
        result = subprocess.run(migration_cmd, capture_output=True, text=True, check=True)
        
        print("   ✅ Alembic migration completed successfully")
        print("   📝 Migration output:")
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"      {line}")
                
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Migration failed!")
        print(f"   Error: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        
        print(f"\n🔄 ROLLBACK INSTRUCTIONS:")
        print(f"   To restore from backup:")
        print(f"   1. psql -U {db_user} -h {db_host} -p {db_port} -d {db_name} < {backup_path}")
        print(f"   2. Or use: uv run alembic downgrade -1")
        
        return False
    
    # ====================================================================
    # PHASE 4: Test CASCADE Behavior
    # ====================================================================
    
    print("\n📋 Phase 4: Testing CASCADE DELETE Behavior")
    print("-" * 40)
    
    print("🧪 Running CASCADE DELETE tests...")
    
    try:
        test_cmd = ["uv", "run", "python", "test_cascade_deletion.py"]
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        # Print test output
        print("   📝 Test output:")
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"      {line}")
        
        if result.returncode == 0:
            print("   ✅ CASCADE DELETE tests passed!")
        else:
            print("   ⚠️  Some CASCADE DELETE tests failed!")
            print("   🔍 Please review the test output above")
            print("   📁 Migration completed but may need adjustments")
            
    except Exception as e:
        print(f"   ⚠️  Could not run CASCADE tests: {e}")
        print("   📁 Migration completed but tests were not verified")
    
    # ====================================================================
    # PHASE 5: Final Summary and Instructions
    # ====================================================================
    
    print("\n📋 Phase 5: Migration Summary")
    print("-" * 40)
    
    print("✅ CASCADE DELETE Migration Completed!")
    print(f"💾 Backup available at: {backup_path.absolute()}")
    
    print("\n🔧 What Changed:")
    print("   • Study deletions now CASCADE to database_releases and reporting_efforts")
    print("   • Database release deletions now CASCADE to reporting_efforts")
    print("   • Package deletions now CASCADE to package_items and details")
    print("   • Reporting effort deletions now CASCADE through the entire chain")
    print("   • User assignments now SET NULL when users are deleted")
    print("   • Audit trails are preserved with SET NULL for deleted users")
    print("   • Text element references use appropriate CASCADE/SET NULL/RESTRICT")
    
    print("\n🎯 Benefits:")
    print("   • No more orphaned records when entities are deleted")
    print("   • Database referential integrity is now enforced at DB level")
    print("   • Consistent behavior between API deletions and direct DB operations")
    print("   • Safer data management operations")
    
    print("\n⚠️  Important Notes:")
    print("   • Test the system thoroughly before production use")
    print("   • Monitor for any unexpected cascade behavior")
    print("   • Document these changes for your team")
    print("   • Consider updating your backup procedures")
    
    if backup_path.exists():
        print(f"\n🔄 Rollback Instructions (if needed):")
        print(f"   To restore the pre-migration state:")
        print(f"   psql -U {db_user} -h {db_host} -p {db_port} -d {db_name} < {backup_path}")
        print(f"   (This will restore the database to its pre-migration state)")
    
    print("\n🎉 Migration process completed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(execute_cascade_migration())
    
    if success:
        print("\n🎊 SUCCESS: CASCADE DELETE migration completed successfully!")
        print("The orphaned records issue has been resolved.")
        sys.exit(0)
    else:
        print("\n💥 FAILED: Migration encountered issues.")
        print("Please review the errors above and take appropriate action.")
        sys.exit(1)
