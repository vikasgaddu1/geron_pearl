#!/usr/bin/env python3
"""
Debug by simulating the exact frontend call to see what's happening.
"""

import asyncio
import httpx
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

async def test_frontend_call():
    """Test the exact call the frontend makes."""
    
    async with httpx.AsyncClient() as client:
        # Get current items first to see what exists
        response = await client.get("http://localhost:8000/api/v1/reporting-effort-items/by-effort/2")
        if response.status_code == 200:
            current_items = response.json()
            print(f"Current items in reporting effort 2: {len(current_items)}")
        
        # Test copy with minimal logging
        copy_data = {"package_id": 1}
        print(f"Sending copy request: {copy_data}")
        
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/reporting-effort-items/2/copy-from-package", 
                json=copy_data,
                timeout=30.0
            )
            
            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error response: {response.text}")
            else:
                result = response.json()
                print(f"Success! Created {len(result)} items")
                
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_frontend_call())