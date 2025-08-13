#!/usr/bin/env python3
"""Debug specific items 36 and 37."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.crud.reporting_effort_item_tracker import reporting_effort_item_tracker
from app.crud.reporting_effort_item import reporting_effort_item

async def debug_specific_items():
    """Debug specific items 36 and 37."""
    
    async with AsyncSessionLocal() as db:
        for item_id in [36, 37]:
            # Check if item exists
            item = await reporting_effort_item.get(db, id=item_id)
            print(f"Item {item_id}: {'EXISTS' if item else 'NOT FOUND'}")
            if item:
                print(f"  Code: {item.item_code}, Type: {item.item_type}")
                
                # Check for tracker
                tracker = await reporting_effort_item_tracker.get_by_item(db, reporting_effort_item_id=item_id)
                print(f"  Tracker: {'ID ' + str(tracker.id) if tracker else 'NOT FOUND'}")
                if tracker:
                    print(f"    Production: {tracker.production_programmer_id}")
                    print(f"    QC: {tracker.qc_programmer_id}")

if __name__ == "__main__":
    asyncio.run(debug_specific_items())