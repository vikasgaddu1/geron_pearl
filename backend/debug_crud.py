#!/usr/bin/env python3
"""Debug script for CRUD operations."""

import asyncio
from app.db.session import AsyncSessionLocal
from app.crud import acronym_set_member, acronym_set
from app.schemas.acronym_set_member import AcronymSetMemberCreate

async def test_crud_operations():
    """Test CRUD operations directly."""
    print("🔍 Testing CRUD operations directly...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Test the problematic get_by_acronym_set_id method
            print("📋 Testing get_by_acronym_set_id with set_id=2...")
            members = await acronym_set_member.get_by_acronym_set_id(db, acronym_set_id=2)
            print(f"✅ Found {len(members)} members")
            
            # Test get_with_members method
            print("📋 Testing get_with_members with set_id=2...")
            set_with_members = await acronym_set.get_with_members(db, acronym_set_id=2)
            if set_with_members:
                print(f"✅ Retrieved set: {set_with_members.name}")
                print(f"   Members: {len(set_with_members.acronyms) if hasattr(set_with_members, 'acronyms') else 'No acronyms attribute'}")
            else:
                print("❌ Set with members not found")
                
        except Exception as e:
            print(f"❌ Error during CRUD operations: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crud_operations())