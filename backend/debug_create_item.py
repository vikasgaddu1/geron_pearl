#!/usr/bin/env python3
"""Debug script to understand the reporting effort item creation issue."""

import asyncio
from app.db.session import AsyncSessionLocal
from app.schemas.reporting_effort_item import ReportingEffortItemCreate
from app.crud.reporting_effort_item import reporting_effort_item

async def debug_create():
    """Debug the item creation process."""
    print("Creating test item data...")
    
    # Create the item data exactly as the API receives it
    item_data = ReportingEffortItemCreate(
        reporting_effort_id=2,
        item_type="TLF",
        item_subtype="Table", 
        item_code="T_14_1_1_DEBUG",
        source_type=None
    )
    
    print(f"Item data created: {item_data}")
    print(f"Item data dict: {item_data.model_dump()}")
    
    # Try to create the item
    async with AsyncSessionLocal() as db:
        try:
            created_item = await reporting_effort_item.create_with_details(
                db,
                obj_in=item_data,
                auto_create_tracker=True
            )
            print(f"✅ SUCCESS: Created item with ID: {created_item.id}")
            return created_item
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    asyncio.run(debug_create())