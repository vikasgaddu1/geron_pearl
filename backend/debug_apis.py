#!/usr/bin/env python3
"""Debug script to test individual API endpoints."""

import asyncio
import httpx
import json

BASE_URL = "http://0.0.0.0:8000/api/v1"

async def test_individual_endpoints():
    """Test each endpoint individually to identify issues."""
    
    async with httpx.AsyncClient() as client:
        print("🔍 Testing individual API endpoints...")
        
        # Test TextElement (we know this works)
        print("\n1. Testing TextElement...")
        response = await client.post(f"{BASE_URL}/text-elements/", json={"type": "title", "label": "Debug Test"})
        print(f"   POST text-elements: {response.status_code}")
        if response.status_code == 201:
            text_element_id = response.json()["id"]
            print(f"   Created text element ID: {text_element_id}")
        
        # Test Acronym
        print("\n2. Testing Acronym...")
        response = await client.post(f"{BASE_URL}/acronyms/", json={"key": "TEST", "value": "Test Value"})
        print(f"   POST acronyms: {response.status_code}")
        if response.status_code == 201:
            acronym_id = response.json()["id"]
            print(f"   Created acronym ID: {acronym_id}")
        else:
            print(f"   Error: {response.text}")
            return
        
        # Test AcronymSet
        print("\n3. Testing AcronymSet...")
        response = await client.post(f"{BASE_URL}/acronym-sets/", json={"name": "Debug Set", "description": "Test set"})
        print(f"   POST acronym-sets: {response.status_code}")
        if response.status_code == 201:
            set_id = response.json()["id"]
            print(f"   Created set ID: {set_id}")
        else:
            print(f"   Error: {response.text}")
            return
        
        # Test AcronymSetMember
        print("\n4. Testing AcronymSetMember...")
        response = await client.post(f"{BASE_URL}/acronym-set-members/", json={
            "acronym_set_id": set_id,
            "acronym_id": acronym_id,
            "sort_order": 0
        })
        print(f"   POST acronym-set-members: {response.status_code}")
        if response.status_code == 201:
            member_id = response.json()["id"]
            print(f"   Created member ID: {member_id}")
        else:
            print(f"   Error: {response.text}")
        
        # Test GET operations
        print("\n5. Testing GET operations...")
        
        response = await client.get(f"{BASE_URL}/acronym-set-members/?acronym_set_id={set_id}")
        print(f"   GET acronym-set-members by set: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
        
        response = await client.get(f"{BASE_URL}/acronym-sets/{set_id}/with-members")
        print(f"   GET acronym-sets with members: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
        
        # Test DELETE operations (should fail due to protection)
        print("\n6. Testing DELETE protection...")
        
        response = await client.delete(f"{BASE_URL}/acronym-sets/{set_id}")
        print(f"   DELETE acronym-set (should fail): {response.status_code}")
        if response.status_code != 400:
            print(f"   Unexpected result: {response.text}")
        else:
            print("   ✅ Deletion protection working")
        
        # Clean up by removing member first
        print("\n7. Testing proper cleanup sequence...")
        
        response = await client.delete(f"{BASE_URL}/acronym-set-members/{member_id}")
        print(f"   DELETE member: {response.status_code}")
        
        response = await client.delete(f"{BASE_URL}/acronym-sets/{set_id}")
        print(f"   DELETE set (should work now): {response.status_code}")
        
        response = await client.delete(f"{BASE_URL}/acronyms/{acronym_id}")
        print(f"   DELETE acronym: {response.status_code}")
        
        response = await client.delete(f"{BASE_URL}/text-elements/{text_element_id}")
        print(f"   DELETE text-element: {response.status_code}")
        
        print("\n✅ Individual endpoint testing completed!")

if __name__ == "__main__":
    asyncio.run(test_individual_endpoints())