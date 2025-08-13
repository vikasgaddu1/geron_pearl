#!/usr/bin/env python3
"""Debug tracker creation and lookup."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.crud.reporting_effort_item_tracker import reporting_effort_item_tracker
from app.crud.reporting_effort_item import reporting_effort_item

async def debug_trackers():
    """Debug tracker creation and lookup."""
    
    async with AsyncSessionLocal() as db:
        # Get recent items
        recent_items = await reporting_effort_item.get_multi(db, skip=0, limit=5)
        print(f"Recent items: {[f'ID:{item.id} Code:{item.item_code}' for item in recent_items]}")
        
        # Check for trackers for these items
        for item in recent_items:
            tracker = await reporting_effort_item_tracker.get_by_item(db, reporting_effort_item_id=item.id)
            print(f"Item {item.id} ({item.item_code}): Tracker = {tracker.id if tracker else 'NONE'}")
            
        # Get all trackers
        all_trackers = await reporting_effort_item_tracker.get_multi(db, skip=0, limit=10)
        print(f"All trackers: {[f'ID:{t.id} ItemID:{t.reporting_effort_item_id}' for t in all_trackers]}")

if __name__ == "__main__":
    asyncio.run(debug_trackers())