#!/usr/bin/env python3
"""
Script to clear all items from a reporting effort for testing purposes.
Usage: python clear_reporting_effort_items.py [reporting_effort_id]
"""

import asyncio
import sys
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.reporting_effort_item import reporting_effort_item
from app.crud import reporting_effort


async def list_reporting_efforts():
    """List all available reporting efforts."""
    async for db in get_db():
        efforts = await reporting_effort.get_multi(db, limit=100)
        
        if not efforts:
            print("No reporting efforts found.")
            return
            
        print("\nAvailable Reporting Efforts:")
        print("=" * 50)
        for effort in efforts:
            print(f"ID: {effort.id} - {effort.database_release_label}")
        print("=" * 50)
        break


async def get_items_count(db: AsyncSession, reporting_effort_id: int) -> int:
    """Get count of items in a reporting effort."""
    items = await reporting_effort_item.get_by_reporting_effort(
        db, reporting_effort_id=reporting_effort_id
    )
    return len(items)


async def clear_reporting_effort_items(reporting_effort_id: int):
    """Clear all items from a specific reporting effort."""
    async for db in get_db():
        # Verify reporting effort exists
        effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not effort:
            print(f"❌ Reporting effort with ID {reporting_effort_id} not found.")
            return False
            
        print(f"🎯 Found reporting effort: {effort.database_release_label}")
        
        # Get all items
        items = await reporting_effort_item.get_by_reporting_effort(
            db, reporting_effort_id=reporting_effort_id
        )
        
        if not items:
            print(f"✅ Reporting effort '{effort.database_release_label}' already has no items.")
            return True
            
        print(f"📋 Found {len(items)} items to delete:")
        
        # Show items before deletion
        for item in items[:5]:  # Show first 5
            print(f"   - {item.item_type.value}: {item.item_code}")
        if len(items) > 5:
            print(f"   - ... and {len(items) - 5} more items")
        
        # Ask for confirmation
        response = input(f"\n❓ Delete all {len(items)} items from '{effort.database_release_label}'? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Deletion cancelled.")
            return False
        
        # Delete all items
        deleted_count = 0
        print(f"\n🗑️  Deleting items...")
        
        for item in items:
            try:
                await reporting_effort_item.delete(db, id=item.id)
                deleted_count += 1
                if deleted_count % 10 == 0:
                    print(f"   Deleted {deleted_count}/{len(items)} items...")
            except Exception as e:
                print(f"❌ Error deleting item {item.id}: {e}")
        
        await db.commit()
        
        print(f"✅ Successfully deleted {deleted_count} items from '{effort.database_release_label}'")
        print(f"🎉 Reporting effort '{effort.database_release_label}' is now ready for testing copy operations!")
        
        return True


async def main():
    if len(sys.argv) < 2:
        print("Usage: python clear_reporting_effort_items.py [reporting_effort_id]")
        print("\nTo see available reporting efforts, run:")
        print("python clear_reporting_effort_items.py list")
        return
    
    if sys.argv[1].lower() == 'list':
        await list_reporting_efforts()
        return
    
    try:
        reporting_effort_id = int(sys.argv[1])
    except ValueError:
        print("❌ Error: reporting_effort_id must be a number")
        return
    
    success = await clear_reporting_effort_items(reporting_effort_id)
    if success:
        print(f"\n🧪 You can now test copy operations with reporting effort ID {reporting_effort_id}")
        print("   The effort should be empty and ready to receive copied items!")


if __name__ == "__main__":
    asyncio.run(main())
