#!/usr/bin/env python3
"""Direct test of reporting effort item creation without API layer."""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.schemas.reporting_effort_item import ReportingEffortItemCreate
from app.crud.reporting_effort_item import reporting_effort_item
from app.crud.reporting_effort import reporting_effort

async def test_item_creation():
    """Test item creation directly via CRUD layer."""
    
    async with AsyncSessionLocal() as db:
        try:
            # First, get an existing reporting effort
            efforts = await reporting_effort.get_multi(db, skip=0, limit=1)
            if not efforts:
                print("ERROR: No reporting efforts found. Create one first.")
                return False
                
            effort_id = efforts[0].id
            print(f"Using reporting effort ID: {effort_id}")
            
            # Create item data
            item_data = ReportingEffortItemCreate(
                reporting_effort_id=effort_id,
                item_type="TLF",
                item_subtype="Table", 
                item_code=f"T_DIRECT_TEST_{asyncio.get_event_loop().time()}",
                source_type="custom"
            )
            
            print(f"Creating item with data: {item_data.model_dump(mode='json')}")
            
            # Create the item
            created_item = await reporting_effort_item.create_with_details(
                db,
                obj_in=item_data,
                auto_create_tracker=True
            )
            
            print(f"SUCCESS: Created item with ID: {created_item.id}")
            print(f"Item details: {created_item}")
            return True
            
        except Exception as e:
            print(f"ERROR during item creation: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    result = asyncio.run(test_item_creation())
    sys.exit(0 if result else 1)