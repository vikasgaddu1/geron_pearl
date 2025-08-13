#!/usr/bin/env python3
"""Check if item 42 has a tracker."""

import asyncio
from app.db.session import AsyncSessionLocal
from app.crud.reporting_effort_item_tracker import reporting_effort_item_tracker

async def check_tracker():
    async with AsyncSessionLocal() as db:
        tracker = await reporting_effort_item_tracker.get_by_item(db, reporting_effort_item_id=42)
        print(f"Tracker for item 42: {'EXISTS' if tracker else 'NOT FOUND'}")
        if tracker:
            print(f"  Tracker ID: {tracker.id}")
            print(f"  Production programmer: {tracker.production_programmer_id}")
            print(f"  QC programmer: {tracker.qc_programmer_id}")

if __name__ == "__main__":
    asyncio.run(check_tracker())