#!/bin/bash

# Test script for Users CRUD operations
# This script tests the complete CRUD functionality for users

API_URL="http://localhost:8000/api/v1"
USERS_URL="${API_URL}/users"

echo "========================================="
echo "PEARL Users CRUD Test Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        echo "Response: $3"
    fi
}

# Test 1: Create an admin user
echo -e "${YELLOW}Test 1: Create Admin User${NC}"
RESPONSE=$(curl -s -X POST "${USERS_URL}/" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "admin_user",
        "role": "ADMIN"
    }')

if echo "$RESPONSE" | grep -q '"username":"admin_user"'; then
    print_result 0 "Admin user created successfully"
    ADMIN_ID=$(echo "$RESPONSE" | sed -n 's/.*"id":\([0-9]*\).*/\1/p')
    echo "Created admin user with ID: $ADMIN_ID"
else
    print_result 1 "Failed to create admin user" "$RESPONSE"
fi
echo ""

# Test 2: Create an editor user
echo -e "${YELLOW}Test 2: Create Editor User${NC}"
RESPONSE=$(curl -s -X POST "${USERS_URL}/" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "editor_user",
        "role": "EDITOR"
    }')

if echo "$RESPONSE" | grep -q '"username":"editor_user"'; then
    print_result 0 "Editor user created successfully"
    EDITOR_ID=$(echo "$RESPONSE" | sed -n 's/.*"id":\([0-9]*\).*/\1/p')
    echo "Created editor user with ID: $EDITOR_ID"
else
    print_result 1 "Failed to create editor user" "$RESPONSE"
fi
echo ""

# Test 3: Create a viewer user
echo -e "${YELLOW}Test 3: Create Viewer User${NC}"
RESPONSE=$(curl -s -X POST "${USERS_URL}/" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "viewer_user",
        "role": "VIEWER"
    }')

if echo "$RESPONSE" | grep -q '"username":"viewer_user"'; then
    print_result 0 "Viewer user created successfully"
    VIEWER_ID=$(echo "$RESPONSE" | sed -n 's/.*"id":\([0-9]*\).*/\1/p')
    echo "Created viewer user with ID: $VIEWER_ID"
else
    print_result 1 "Failed to create viewer user" "$RESPONSE"
fi
echo ""

# Test 4: Test duplicate username prevention
echo -e "${YELLOW}Test 4: Test Duplicate Username Prevention${NC}"
RESPONSE=$(curl -s -X POST "${USERS_URL}/" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "admin_user",
        "role": "VIEWER"
    }')

if echo "$RESPONSE" | grep -q "already exists"; then
    print_result 0 "Duplicate username correctly prevented"
else
    print_result 1 "Failed to prevent duplicate username" "$RESPONSE"
fi
echo ""

# Test 5: Get all users
echo -e "${YELLOW}Test 5: Get All Users${NC}"
RESPONSE=$(curl -s -X GET "${USERS_URL}/")

if echo "$RESPONSE" | grep -q '"admin_user"' && echo "$RESPONSE" | grep -q '"editor_user"' && echo "$RESPONSE" | grep -q '"viewer_user"'; then
    print_result 0 "Retrieved all users successfully"
    USER_COUNT=$(echo "$RESPONSE" | grep -o '"username"' | wc -l)
    echo "Total users in system: $USER_COUNT"
else
    print_result 1 "Failed to retrieve all users" "$RESPONSE"
fi
echo ""

# Test 6: Get user by ID
echo -e "${YELLOW}Test 6: Get User by ID${NC}"
if [ ! -z "$ADMIN_ID" ]; then
    RESPONSE=$(curl -s -X GET "${USERS_URL}/${ADMIN_ID}")
    
    if echo "$RESPONSE" | grep -q '"username":"admin_user"'; then
        print_result 0 "Retrieved user by ID successfully"
    else
        print_result 1 "Failed to retrieve user by ID" "$RESPONSE"
    fi
else
    echo "Skipping - No user ID available"
fi
echo ""

# Test 7: Update user
echo -e "${YELLOW}Test 7: Update User${NC}"
if [ ! -z "$EDITOR_ID" ]; then
    RESPONSE=$(curl -s -X PUT "${USERS_URL}/${EDITOR_ID}" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "senior_editor",
            "role": "EDITOR"
        }')
    
    if echo "$RESPONSE" | grep -q '"username":"senior_editor"'; then
        print_result 0 "User updated successfully"
    else
        print_result 1 "Failed to update user" "$RESPONSE"
    fi
else
    echo "Skipping - No user ID available"
fi
echo ""

# Test 8: Update user role only
echo -e "${YELLOW}Test 8: Update User Role Only${NC}"
if [ ! -z "$VIEWER_ID" ]; then
    RESPONSE=$(curl -s -X PUT "${USERS_URL}/${VIEWER_ID}" \
        -H "Content-Type: application/json" \
        -d '{
            "role": "EDITOR"
        }')
    
    if echo "$RESPONSE" | grep -q '"role":"EDITOR"'; then
        print_result 0 "User role updated successfully"
    else
        print_result 1 "Failed to update user role" "$RESPONSE"
    fi
else
    echo "Skipping - No user ID available"
fi
echo ""

# Test 9: Test duplicate username on update
echo -e "${YELLOW}Test 9: Test Duplicate Username on Update${NC}"
if [ ! -z "$VIEWER_ID" ]; then
    RESPONSE=$(curl -s -X PUT "${USERS_URL}/${VIEWER_ID}" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "admin_user"
        }')
    
    if echo "$RESPONSE" | grep -q "already exists"; then
        print_result 0 "Duplicate username correctly prevented on update"
    else
        print_result 1 "Failed to prevent duplicate username on update" "$RESPONSE"
    fi
else
    echo "Skipping - No user ID available"
fi
echo ""

# Test 10: Delete users
echo -e "${YELLOW}Test 10: Delete Users${NC}"

# Delete viewer user
if [ ! -z "$VIEWER_ID" ]; then
    RESPONSE=$(curl -s -X DELETE "${USERS_URL}/${VIEWER_ID}")
    
    if echo "$RESPONSE" | grep -q '"username"'; then
        print_result 0 "Viewer user deleted successfully"
    else
        print_result 1 "Failed to delete viewer user" "$RESPONSE"
    fi
fi

# Delete editor user
if [ ! -z "$EDITOR_ID" ]; then
    RESPONSE=$(curl -s -X DELETE "${USERS_URL}/${EDITOR_ID}")
    
    if echo "$RESPONSE" | grep -q '"username"'; then
        print_result 0 "Editor user deleted successfully"
    else
        print_result 1 "Failed to delete editor user" "$RESPONSE"
    fi
fi

# Delete admin user
if [ ! -z "$ADMIN_ID" ]; then
    RESPONSE=$(curl -s -X DELETE "${USERS_URL}/${ADMIN_ID}")
    
    if echo "$RESPONSE" | grep -q '"username"'; then
        print_result 0 "Admin user deleted successfully"
    else
        print_result 1 "Failed to delete admin user" "$RESPONSE"
    fi
fi
echo ""

# Test 11: Verify all users deleted
echo -e "${YELLOW}Test 11: Verify All Test Users Deleted${NC}"
RESPONSE=$(curl -s -X GET "${USERS_URL}/")

if ! echo "$RESPONSE" | grep -q '"admin_user"' && ! echo "$RESPONSE" | grep -q '"editor_user"' && ! echo "$RESPONSE" | grep -q '"viewer_user"' && ! echo "$RESPONSE" | grep -q '"senior_editor"'; then
    print_result 0 "All test users successfully deleted"
else
    print_result 1 "Some test users still exist" "$RESPONSE"
fi
echo ""

echo "========================================="
echo "Users CRUD tests completed!"
echo "========================================="