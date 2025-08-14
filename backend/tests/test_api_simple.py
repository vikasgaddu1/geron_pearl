#!/usr/bin/env python3
"""Test the API endpoint directly with Python requests."""

import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_item_creation():
    """Test item creation via API."""
    
    # Create unique item code
    unique_code = f"T_API_TEST_{int(time.time())}"
    
    payload = {
        "reporting_effort_id": 13,
        "item_type": "TLF",
        "item_subtype": "Table", 
        "item_code": unique_code,
        "source_type": "custom"
    }
    
    print(f"Sending request with payload: {payload}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/reporting-effort-items/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"SUCCESS: Created item with ID: {data.get('id', 'NOT_FOUND')}")
            return True
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_item_creation()