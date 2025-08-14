#!/usr/bin/env python3
"""Test if items are actually being created and persisted."""

import asyncio
import requests
import time

async def test_creation_and_verification():
    """Test item creation and verify it exists."""
    
    unique_code = f"T_VERIFY_CREATION_{int(time.time())}"
    
    # Create item via API
    print(f"Creating item with code: {unique_code}")
    response = requests.post(
        "http://localhost:8000/api/v1/reporting-effort-items/",
        json={
            "reporting_effort_id": 2,
            "item_type": "TLF",
            "item_subtype": "Table",
            "item_code": unique_code,
            "source_type": "custom"
        }
    )
    
    print(f"API Response: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        item_id = data.get('id')
        print(f"API says item created with ID: {item_id}")
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Try to retrieve it via API
        get_response = requests.get(f"http://localhost:8000/api/v1/reporting-effort-items/{item_id}")
        print(f"GET Response: {get_response.status_code}")
        if get_response.status_code == 200:
            print(f"Item verified via API: {get_response.json()}")
        else:
            print(f"Item NOT found via API: {get_response.text}")
            
        # Check via database directly
        from app.db.session import AsyncSessionLocal
        from app.crud.reporting_effort_item import reporting_effort_item
        
        async with AsyncSessionLocal() as db:
            db_item = await reporting_effort_item.get(db, id=item_id)
            print(f"Database direct lookup: {'FOUND' if db_item else 'NOT FOUND'}")
            if db_item:
                print(f"  Code: {db_item.item_code}")
                print(f"  Type: {db_item.item_type}")
                
    else:
        print(f"API Error: {response.text}")

if __name__ == "__main__":
    try:
        import requests
        asyncio.run(test_creation_and_verification())
    except ImportError:
        print("requests not available, using curl test")
        # Fallback curl test will be handled by caller
