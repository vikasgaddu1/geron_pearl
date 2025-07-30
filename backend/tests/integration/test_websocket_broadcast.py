#!/usr/bin/env python3
"""
Test WebSocket broadcasting by making CRUD operations via HTTP API
"""

import asyncio
import json
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def create_study(label):
    """Create a study via HTTP API"""
    response = requests.post(f"{BASE_URL}/studies/", 
                           json={"study_label": label})
    print(f"Create study '{label}': {response.status_code}")
    if response.status_code == 201:
        return response.json()
    return None

def update_study(study_id, label):
    """Update a study via HTTP API"""
    response = requests.put(f"{BASE_URL}/studies/{study_id}", 
                          json={"study_label": label})
    print(f"Update study {study_id} to '{label}': {response.status_code}")
    return response.status_code == 200

def delete_study(study_id):
    """Delete a study via HTTP API"""
    response = requests.delete(f"{BASE_URL}/studies/{study_id}")
    print(f"Delete study {study_id}: {response.status_code}")
    return response.status_code == 200

def main():
    print("🧪 Testing WebSocket broadcasting with CRUD operations...")
    print("👀 Watch your frontend for real-time updates!")
    
    # Test 1: Create a study
    print("\n1️⃣ Creating a test study...")
    study = create_study("WebSocket Test Study")
    if not study:
        print("❌ Failed to create study")
        return
    
    study_id = study["id"]
    print(f"✅ Created study with ID: {study_id}")
    time.sleep(2)
    
    # Test 2: Update the study
    print("\n2️⃣ Updating the study...")
    if update_study(study_id, "Updated WebSocket Test"):
        print("✅ Study updated")
    else:
        print("❌ Failed to update study")
    time.sleep(2)
    
    # Test 3: Delete the study
    print("\n3️⃣ Deleting the study...")
    if delete_study(study_id):
        print("✅ Study deleted")
    else:
        print("❌ Failed to delete study")
    
    print("\n🎉 Test completed! Check your frontend for real-time updates.")

if __name__ == "__main__":
    main()