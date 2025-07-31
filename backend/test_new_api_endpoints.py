#!/usr/bin/env python3
"""Test script for new TNFP and Acronym API endpoints."""

import asyncio
import json
import httpx
from typing import List, Dict, Any

BASE_URL = "http://0.0.0.0:8000/api/v1"

async def test_text_elements():
    """Test TextElement CRUD operations."""
    print("\n🔵 Testing TextElement endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test create text element
        text_element_data = {
            "type": "title",
            "label": "Study Summary Report Title"
        }
        
        print("  📝 Creating text element...")
        response = await client.post(f"{BASE_URL}/text-elements/", json=text_element_data)
        print(f"    Status: {response.status_code}")
        if response.status_code == 201:
            created_element = response.json()
            element_id = created_element["id"]
            print(f"    Created: {created_element['type']} - {created_element['label'][:50]}... (ID: {element_id})")
            
            # Test get text element
            print("  📄 Retrieving text element...")
            response = await client.get(f"{BASE_URL}/text-elements/{element_id}")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                retrieved_element = response.json()
                print(f"    Retrieved: {retrieved_element['type']} - {retrieved_element['label'][:50]}...")
            
            # Test update text element
            print("  ✏️ Updating text element...")
            update_data = {"label": "Updated Study Summary Report Title"}
            response = await client.put(f"{BASE_URL}/text-elements/{element_id}", json=update_data)
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                updated_element = response.json()
                print(f"    Updated: {updated_element['label'][:50]}...")
            
            # Test list text elements
            print("  📋 Listing text elements...")
            response = await client.get(f"{BASE_URL}/text-elements/")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                elements = response.json()
                print(f"    Found {len(elements)} text elements")
            
            # Test search text elements
            print("  🔍 Searching text elements...")
            response = await client.get(f"{BASE_URL}/text-elements/search?q=Study")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                search_results = response.json()
                print(f"    Search results: {len(search_results)} elements")
            
            # Test delete text element
            print("  🗑️ Deleting text element...")
            response = await client.delete(f"{BASE_URL}/text-elements/{element_id}")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                deleted_element = response.json()
                print(f"    Deleted: {deleted_element['type']} - ID {deleted_element['id']}")
        else:
            print(f"    Error creating text element: {response.text}")


async def test_acronyms():
    """Test Acronym CRUD operations."""
    print("\n🔵 Testing Acronym endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test create acronym
        acronym_data = {
            "key": "USA",
            "value": "United States of America",
            "description": "Country in North America"
        }
        
        print("  📝 Creating acronym...")
        response = await client.post(f"{BASE_URL}/acronyms/", json=acronym_data)
        print(f"    Status: {response.status_code}")
        if response.status_code == 201:
            created_acronym = response.json()
            acronym_id = created_acronym["id"]
            print(f"    Created: {created_acronym['key']} = {created_acronym['value']} (ID: {acronym_id})")
            
            # Test get acronym
            print("  📄 Retrieving acronym...")
            response = await client.get(f"{BASE_URL}/acronyms/{acronym_id}")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                retrieved_acronym = response.json()
                print(f"    Retrieved: {retrieved_acronym['key']} = {retrieved_acronym['value']}")
            
            # Test update acronym
            print("  ✏️ Updating acronym...")
            update_data = {"value": "United States"}
            response = await client.put(f"{BASE_URL}/acronyms/{acronym_id}", json=update_data)
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                updated_acronym = response.json()
                print(f"    Updated: {updated_acronym['key']} = {updated_acronym['value']}")
            
            # Test list acronyms
            print("  📋 Listing acronyms...")
            response = await client.get(f"{BASE_URL}/acronyms/")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                acronyms = response.json()
                print(f"    Found {len(acronyms)} acronyms")
            
            # Test search acronyms
            print("  🔍 Searching acronyms...")
            response = await client.get(f"{BASE_URL}/acronyms/search?q=United")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                search_results = response.json()
                print(f"    Search results: {len(search_results)} acronyms")
            
            # Test delete acronym (save for later)
            return acronym_id
        else:
            print(f"    Error creating acronym: {response.text}")
            return None


async def test_acronym_sets_and_members():
    """Test AcronymSet and AcronymSetMember CRUD operations."""
    print("\n🔵 Testing AcronymSet and AcronymSetMember endpoints...")
    
    async with httpx.AsyncClient() as client:
        # First create another acronym
        acronym_data = {
            "key": "UK",
            "value": "United Kingdom",
            "description": "Country in Europe"
        }
        
        print("  📝 Creating second acronym...")
        response = await client.post(f"{BASE_URL}/acronyms/", json=acronym_data)
        uk_acronym_id = None
        if response.status_code == 201:
            uk_acronym = response.json()
            uk_acronym_id = uk_acronym["id"]
            print(f"    Created: {uk_acronym['key']} = {uk_acronym['value']} (ID: {uk_acronym_id})")
        
        # Create acronym set
        set_data = {
            "name": "Countries",
            "description": "Set of country acronyms"
        }
        
        print("  📝 Creating acronym set...")
        response = await client.post(f"{BASE_URL}/acronym-sets/", json=set_data)
        print(f"    Status: {response.status_code}")
        if response.status_code == 201:
            created_set = response.json()
            set_id = created_set["id"]
            print(f"    Created set: {created_set['name']} (ID: {set_id})")
            
            # Test get acronym set
            print("  📄 Retrieving acronym set...")
            response = await client.get(f"{BASE_URL}/acronym-sets/{set_id}")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                retrieved_set = response.json()
                print(f"    Retrieved: {retrieved_set['name']}")
            
            # Test list acronym sets
            print("  📋 Listing acronym sets...")
            response = await client.get(f"{BASE_URL}/acronym-sets/")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                sets = response.json()
                print(f"    Found {len(sets)} acronym sets")
            
            # Test adding acronyms to set (if we have acronym IDs)
            usa_acronym_id = await test_acronyms()  # This returns the USA acronym ID
            if usa_acronym_id and uk_acronym_id:
                print("  📝 Adding acronyms to set...")
                
                # Add USA acronym to set
                member_data = {
                    "acronym_set_id": set_id,
                    "acronym_id": usa_acronym_id,
                    "sort_order": 0
                }
                response = await client.post(f"{BASE_URL}/acronym-set-members/", json=member_data)
                print(f"    USA member status: {response.status_code}")
                
                # Add UK acronym to set
                member_data = {  
                    "acronym_set_id": set_id,
                    "acronym_id": uk_acronym_id,
                    "sort_order": 1
                }
                response = await client.post(f"{BASE_URL}/acronym-set-members/", json=member_data)
                print(f"    UK member status: {response.status_code}")
                
                # Test bulk add
                print("  📦 Testing bulk add...")
                response = await client.post(f"{BASE_URL}/acronym-set-members/bulk-add?acronym_set_id={set_id}", json=[])
                print(f"    Bulk add status: {response.status_code}")
                
                # Get set with members
                print("  📄 Retrieving set with members...")
                response = await client.get(f"{BASE_URL}/acronym-sets/{set_id}/with-members")
                print(f"    Status: {response.status_code}")
                if response.status_code == 200:
                    set_with_members = response.json()
                    print(f"    Set '{set_with_members['name']}' has {len(set_with_members.get('acronyms', []))} members")
                
                # Clean up acronyms
                print("  🗑️ Cleaning up acronyms...")
                await client.delete(f"{BASE_URL}/acronyms/{usa_acronym_id}")
                await client.delete(f"{BASE_URL}/acronyms/{uk_acronym_id}")
            
            # Test delete acronym set
            print("  🗑️ Deleting acronym set...")
            response = await client.delete(f"{BASE_URL}/acronym-sets/{set_id}")
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                deleted_set = response.json()
                print(f"    Deleted set: {deleted_set['name']} - ID {deleted_set['id']}")
        else:
            print(f"    Error creating acronym set: {response.text}")


async def test_api_documentation():
    """Test API documentation endpoint."""
    print("\n🔵 Testing API documentation...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/docs")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ API documentation is accessible")
        else:
            print("  ❌ API documentation not accessible")


async def main():
    """Run all tests."""
    print("🚀 Testing new TNFP and Acronym API endpoints...")
    print("📋 Make sure the development server is running: uv run python run.py")
    
    try:
        await test_text_elements()
        await test_acronym_sets_and_members()  # This also tests acronyms
        await test_api_documentation()
        
        print("\n✅ All tests completed!")
        print("🌐 Check the API documentation at: http://localhost:8000/docs")
        
    except httpx.ConnectError:
        print("\n❌ Could not connect to the development server.")
        print("   Please start the server with: uv run python run.py")
    except Exception as e:
        print(f"\n❌ Test error: {e}")


if __name__ == "__main__":
    asyncio.run(main())