"""
Test script for comment feature with authentication.
Tests that comments are properly associated with logged-in users.
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test user credentials
TEST_USERS = {
    "admin": {"username": "test_admin", "password": "password123"},
    "editor": {"username": "test_editor", "password": "password123"},
    "viewer": {"username": "test_viewer", "password": "password123"},
}


async def login(username: str, password: str) -> str:
    """Login and get access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
        data = response.json()
        return data["access_token"]


async def get_trackers(token: str) -> list:
    """Get list of trackers."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/reporting-effort-tracker/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise Exception(f"Failed to get trackers: {response.status_code} - {response.text}")
        return response.json()


async def create_comment(token: str, tracker_id: int, comment_text: str, comment_type: str = "programming") -> dict:
    """Create a comment."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/tracker-comments/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "tracker_id": tracker_id,
                "comment_text": comment_text,
                "comment_type": comment_type
            }
        )
        if response.status_code != 201:
            raise Exception(f"Failed to create comment: {response.status_code} - {response.text}")
        return response.json()


async def get_comments(token: str, tracker_id: int) -> list:
    """Get comments for a tracker."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/tracker-comments/tracker/{tracker_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise Exception(f"Failed to get comments: {response.status_code} - {response.text}")
        return response.json()


async def get_current_user(token: str) -> dict:
    """Get current user info."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise Exception(f"Failed to get user: {response.status_code} - {response.text}")
        return response.json()


async def test_comment_feature():
    """Test comment feature with different users."""
    print("=" * 80)
    print("Testing Comment Feature with Authentication")
    print("=" * 80)
    
    try:
        # Test 1: Login as admin
        print("\n1. Logging in as test_admin...")
        admin_token = await login(TEST_USERS["admin"]["username"], TEST_USERS["admin"]["password"])
        admin_user = await get_current_user(admin_token)
        print(f"   [OK] Logged in as: {admin_user['username']} (ID: {admin_user['id']}, Role: {admin_user['role']})")
        
        # Test 2: Get a tracker
        print("\n2. Getting trackers...")
        trackers = await get_trackers(admin_token)
        if not trackers:
            print("   [WARNING] No trackers found. Please create a tracker first.")
            return
        
        tracker = trackers[0]
        tracker_id = tracker["id"]
        print(f"   [OK] Using tracker ID: {tracker_id}")
        
        # Test 3: Create comment as admin
        print(f"\n3. Creating comment as {admin_user['username']}...")
        admin_comment = await create_comment(
            admin_token,
            tracker_id,
            f"This is a test comment from {admin_user['username']}",
            "programming"
        )
        print(f"   [OK] Comment created!")
        print(f"     Comment ID: {admin_comment['id']}")
        print(f"     User ID: {admin_comment['user_id']}")
        print(f"     Username: {admin_comment['username']}")
        print(f"     Text: {admin_comment['comment_text'][:50]}...")
        
        # Verify comment is associated with admin
        assert admin_comment['user_id'] == admin_user['id'], \
            f"Comment user_id ({admin_comment['user_id']}) doesn't match logged-in user ({admin_user['id']})"
        assert admin_comment['username'] == admin_user['username'], \
            f"Comment username ({admin_comment['username']}) doesn't match logged-in user ({admin_user['username']})"
        print(f"   [OK] Comment correctly associated with {admin_user['username']}")
        
        # Test 4: Login as editor
        print("\n4. Logging in as test_editor...")
        editor_token = await login(TEST_USERS["editor"]["username"], TEST_USERS["editor"]["password"])
        editor_user = await get_current_user(editor_token)
        print(f"   [OK] Logged in as: {editor_user['username']} (ID: {editor_user['id']}, Role: {editor_user['role']})")
        
        # Test 5: Create comment as editor
        print(f"\n5. Creating comment as {editor_user['username']}...")
        editor_comment = await create_comment(
            editor_token,
            tracker_id,
            f"This is a test comment from {editor_user['username']}",
            "biostat"
        )
        print(f"   [OK] Comment created!")
        print(f"     Comment ID: {editor_comment['id']}")
        print(f"     User ID: {editor_comment['user_id']}")
        print(f"     Username: {editor_comment['username']}")
        print(f"     Text: {editor_comment['comment_text'][:50]}...")
        
        # Verify comment is associated with editor
        assert editor_comment['user_id'] == editor_user['id'], \
            f"Comment user_id ({editor_comment['user_id']}) doesn't match logged-in user ({editor_user['id']})"
        assert editor_comment['username'] == editor_user['username'], \
            f"Comment username ({editor_comment['username']}) doesn't match logged-in user ({editor_user['username']})"
        print(f"   [OK] Comment correctly associated with {editor_user['username']}")
        
        # Test 6: Get all comments and verify
        print("\n6. Retrieving all comments for tracker...")
        all_comments = await get_comments(editor_token, tracker_id)
        print(f"   [OK] Found {len(all_comments)} comment(s)")
        
        for comment in all_comments:
            print(f"     - Comment {comment['id']}: by {comment['username']} (ID: {comment['user_id']})")
            print(f"       Text: {comment['comment_text'][:50]}...")
        
        # Verify we have both comments
        comment_usernames = [c['username'] for c in all_comments]
        assert TEST_USERS["admin"]["username"] in comment_usernames, "Admin comment not found"
        assert TEST_USERS["editor"]["username"] in comment_usernames, "Editor comment not found"
        print(f"   [OK] Both comments found with correct usernames")
        
        # Test 7: Login as viewer and verify they can see comments
        print("\n7. Logging in as test_viewer...")
        viewer_token = await login(TEST_USERS["viewer"]["username"], TEST_USERS["viewer"]["password"])
        viewer_user = await get_current_user(viewer_token)
        print(f"   [OK] Logged in as: {viewer_user['username']} (ID: {viewer_user['id']}, Role: {viewer_user['role']})")
        
        viewer_comments = await get_comments(viewer_token, tracker_id)
        print(f"   [OK] Viewer can see {len(viewer_comments)} comment(s)")
        
        # Test 8: Create comment as viewer
        print(f"\n8. Creating comment as {viewer_user['username']}...")
        viewer_comment = await create_comment(
            viewer_token,
            tracker_id,
            f"This is a test comment from {viewer_user['username']}",
            "programming"
        )
        print(f"   [OK] Comment created!")
        print(f"     Comment ID: {viewer_comment['id']}")
        print(f"     User ID: {viewer_comment['user_id']}")
        print(f"     Username: {viewer_comment['username']}")
        print(f"     Text: {viewer_comment['comment_text'][:50]}...")
        
        # Verify comment is associated with viewer
        assert viewer_comment['user_id'] == viewer_user['id'], \
            f"Comment user_id ({viewer_comment['user_id']}) doesn't match logged-in user ({viewer_user['id']})"
        assert viewer_comment['username'] == viewer_user['username'], \
            f"Comment username ({viewer_comment['username']}) doesn't match logged-in user ({viewer_user['username']})"
        print(f"   [OK] Comment correctly associated with {viewer_user['username']}")
        
        # Final verification
        print("\n9. Final verification - All comments...")
        final_comments = await get_comments(admin_token, tracker_id)
        print(f"   [OK] Total comments: {len(final_comments)}")
        
        for comment in final_comments:
            print(f"     - Comment {comment['id']}: '{comment['comment_text'][:40]}...'")
            print(f"       Created by: {comment['username']} (User ID: {comment['user_id']})")
            print(f"       Type: {comment['comment_type']}, Resolved: {comment['is_resolved']}")
        
        print("\n" + "=" * 80)
        print("[SUCCESS] All tests passed! Comment feature is working correctly.")
        print("=" * 80)
        print("\nSummary:")
        print(f"  - Created {len(final_comments)} comment(s)")
        print(f"  - Comments correctly associated with logged-in users")
        print(f"  - Usernames displayed correctly")
        print(f"  - All users can create and view comments")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(test_comment_feature())

