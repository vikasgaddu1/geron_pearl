#!/usr/bin/env python3
"""Check if item 42 exists in database."""

import asyncio
from app.db.session import AsyncSessionLocal
from app.crud.reporting_effort_item import reporting_effort_item

async def check_item():
    async with AsyncSessionLocal() as db:
        item = await reporting_effort_item.get(db, id=42)
        print(f"Item 42: {'EXISTS' if item else 'NOT FOUND'}")
        if item:
            print(f"  Code: {item.item_code}")
            print(f"  Type: {item.item_type}")
            print(f"  Created: {item.created_at}")

if __name__ == "__main__":
    asyncio.run(check_item())