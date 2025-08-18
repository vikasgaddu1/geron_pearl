#!/bin/bash

# Comprehensive test script for the Reporting Effort Tracker DELETE endpoint
# Tests the DELETE /api/v1/reporting-effort-tracker/{tracker_id} endpoint

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL for the API
BASE_URL="http://localhost:8000/api/v1"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run a test
run_test() {
    local test_name="$1"
    local expected_code="$2"
    local url="$3"
    local method="$4"
    local data="$5"
    local description="$6"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${BLUE}Test $TESTS_RUN: $test_name${NC}"
    echo "Description: $description"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url")
    fi
    
    # Split response and status code
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    echo "Expected: $expected_code, Got: $http_code"
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        if [ -n "$response_body" ]; then
            echo "Response: $response_body"
        fi
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "Response: $response_body"
        return 1
    fi
}

# Helper function to extract JSON value
extract_json_value() {
    echo "$1" | grep -o "\"$2\":[^,}]*" | cut -d':' -f2 | tr -d '"' | tr -d ' '
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Testing Tracker DELETE Endpoint${NC}"
echo -e "${YELLOW}========================================${NC}"

# Check if server is running
echo -e "\n${YELLOW}Checking if server is running...${NC}"
if ! curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" | grep -q "200"; then
    echo -e "${RED}❌ Server is not running on $BASE_URL${NC}"
    echo -e "${YELLOW}Please start the server with:${NC}"
    echo -e "  ${BLUE}cd C:/python/PEARL/backend${NC}"
    echo -e "  ${BLUE}uv run python run.py${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Server is running and healthy${NC}"

# SETUP: Create test environment
echo -e "\n${YELLOW}======= SETUP: Creating test environment =======${NC}"

# Create test study
study_response=$(curl -s -X POST "$BASE_URL/studies/" \
    -H "Content-Type: application/json" \
    -d '{
        "study_label": "Test Study for Tracker Delete",
        "study_name": "Tracker Delete Test Study"
    }')
STUDY_ID=$(extract_json_value "$study_response" "id")
echo -e "${GREEN}✓ Created test study with ID: $STUDY_ID${NC}"

# Create database release
db_release_response=$(curl -s -X POST "$BASE_URL/database-releases/" \
    -H "Content-Type: application/json" \
    -d '{
        "study_id": '$STUDY_ID',
        "database_release_label": "Test DB Release for Tracker Delete",
        "database_release_date": "2024-01-01"
    }')
DB_RELEASE_ID=$(extract_json_value "$db_release_response" "id")
echo -e "${GREEN}✓ Created database release with ID: $DB_RELEASE_ID${NC}"

# Create reporting effort
effort_response=$(curl -s -X POST "$BASE_URL/reporting-efforts/" \
    -H "Content-Type: application/json" \
    -d '{
        "database_release_id": '$DB_RELEASE_ID',
        "study_id": '$STUDY_ID',
        "database_release_label": "Test Reporting Effort for Tracker Delete"
    }')
EFFORT_ID=$(extract_json_value "$effort_response" "id")
echo -e "${GREEN}✓ Created reporting effort with ID: $EFFORT_ID${NC}"

# Create test user for assignments
user_response=$(curl -s -X POST "$BASE_URL/users/" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "test_programmer_delete",
        "email": "test.delete@example.com",
        "full_name": "Test Delete Programmer",
        "role": "EDITOR",
        "department": "Programming"
    }')
USER_ID=$(extract_json_value "$user_response" "id")
echo -e "${GREEN}✓ Created test user with ID: $USER_ID${NC}"

# Create test reporting effort item
item_response=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
    -H "Content-Type: application/json" \
    -d '{
        "reporting_effort_id": '$EFFORT_ID',
        "item_type": "TLF",
        "item_subtype": "Table",
        "item_code": "T_DELETE_TEST",
        "source_type": "custom"
    }')
ITEM_ID=$(extract_json_value "$item_response" "id")
echo -e "${GREEN}✓ Created test item with ID: $ITEM_ID${NC}"

# Create tracker manually
tracker_response=$(curl -s -X POST "$BASE_URL/reporting-effort-tracker/" \
    -H "Content-Type: application/json" \
    -d '{
        "reporting_effort_item_id": '$ITEM_ID',
        "priority": "medium",
        "production_status": "not_started",
        "qc_status": "not_started"
    }')
TRACKER_ID=$(extract_json_value "$tracker_response" "id")
echo -e "${GREEN}✓ Created tracker with ID: $TRACKER_ID${NC}"

# Create a second item and tracker for deletion verification test
item2_response=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
    -H "Content-Type: application/json" \
    -d '{
        "reporting_effort_id": '$EFFORT_ID',
        "item_type": "Dataset",
        "item_subtype": "ADaM", 
        "item_code": "ADSL_DELETE_TEST",
        "source_type": "custom"
    }')
ITEM2_ID=$(extract_json_value "$item2_response" "id")

tracker2_response=$(curl -s -X POST "$BASE_URL/reporting-effort-tracker/" \
    -H "Content-Type: application/json" \
    -d '{
        "reporting_effort_item_id": '$ITEM2_ID',
        "priority": "medium",
        "production_status": "not_started",
        "qc_status": "not_started"
    }')
TRACKER2_ID=$(extract_json_value "$tracker2_response" "id")
echo -e "${GREEN}✓ Created second tracker with ID: $TRACKER2_ID for deletion verification${NC}"

echo -e "${GREEN}Setup complete!${NC}\n"

# TEST CASES
echo -e "${YELLOW}======= RUNNING DELETE ENDPOINT TESTS =======${NC}"

# Test 1: DELETE non-existent tracker (should return 404)
run_test \
    "Delete Non-Existent Tracker" \
    "404" \
    "$BASE_URL/reporting-effort-tracker/99999" \
    "DELETE" \
    "" \
    "Attempting to delete a tracker that doesn't exist should return 404"

# Test 2: DELETE with invalid tracker ID - non-numeric (should return 422)
run_test \
    "Delete Invalid ID (non-numeric)" \
    "422" \
    "$BASE_URL/reporting-effort-tracker/invalid_id" \
    "DELETE" \
    "" \
    "Using non-numeric tracker ID should return validation error"

# Test 3: DELETE with invalid tracker ID - negative number (should return 404)
run_test \
    "Delete Invalid ID (negative)" \
    "404" \
    "$BASE_URL/reporting-effort-tracker/-1" \
    "DELETE" \
    "" \
    "Using negative tracker ID should return 404 (not found)"

# Test 4: DELETE with zero ID (should return 404)
run_test \
    "Delete Invalid ID (zero)" \
    "404" \
    "$BASE_URL/reporting-effort-tracker/0" \
    "DELETE" \
    "" \
    "Using zero as tracker ID should return 404 (not found)"

# Test 5: DELETE existing tracker with assignments (should succeed with 204)
# First assign a programmer to make it more realistic
assign_response=$(curl -s -X POST "$BASE_URL/reporting-effort-tracker/$TRACKER_ID/assign-programmer" \
    -H "Content-Type: application/json" \
    -d '{
        "user_id": '$USER_ID',
        "role": "production"
    }')
echo -e "${BLUE}Assigned programmer to tracker for deletion test${NC}"

run_test \
    "Delete Existing Tracker with Assignment" \
    "204" \
    "$BASE_URL/reporting-effort-tracker/$TRACKER_ID" \
    "DELETE" \
    "" \
    "Deleting an existing tracker should return 204 No Content"

# Test 6: Verify tracker is actually deleted (should return 404)
run_test \
    "Verify Tracker Deletion" \
    "404" \
    "$BASE_URL/reporting-effort-tracker/$TRACKER_ID" \
    "GET" \
    "" \
    "Attempting to get deleted tracker should return 404"

# Test 7: DELETE another existing tracker (clean deletion without assignments)
run_test \
    "Delete Clean Tracker" \
    "204" \
    "$BASE_URL/reporting-effort-tracker/$TRACKER2_ID" \
    "DELETE" \
    "" \
    "Deleting tracker without assignments should return 204 No Content"

# Test 8: Attempt to delete the same tracker again (should return 404)
run_test \
    "Delete Already Deleted Tracker" \
    "404" \
    "$BASE_URL/reporting-effort-tracker/$TRACKER2_ID" \
    "DELETE" \
    "" \
    "Attempting to delete an already deleted tracker should return 404"

# Test 9: Database verification - ensure tracker by item lookup fails
echo -e "\n${BLUE}Test 9: Database Verification - Tracker by Item Lookup${NC}"
echo "Description: Verify that tracker lookup by item ID fails after deletion"
TESTS_RUN=$((TESTS_RUN + 1))

# Try to get tracker by item ID (should return 404 since tracker is deleted)
verification_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/reporting-effort-tracker/by-item/$ITEM_ID")
verification_code=$(echo "$verification_response" | tail -n1)
verification_body=$(echo "$verification_response" | sed '$d')

echo "Expected: 404, Got: $verification_code"
if [ "$verification_code" = "404" ]; then
    echo -e "${GREEN}✓ PASSED - Tracker properly removed from database${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAILED - Tracker still exists in database${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "Response: $verification_body"
fi

echo -e "\n${YELLOW}======= CLEANUP: Removing test data =======${NC}"

# Delete test items (remaining trackers will be auto-deleted)
curl -s -X DELETE "$BASE_URL/reporting-effort-items/$ITEM_ID" > /dev/null
curl -s -X DELETE "$BASE_URL/reporting-effort-items/$ITEM2_ID" > /dev/null
echo -e "${GREEN}✓ Deleted test items${NC}"

# Delete reporting effort
curl -s -X DELETE "$BASE_URL/reporting-efforts/$EFFORT_ID" > /dev/null
echo -e "${GREEN}✓ Deleted reporting effort${NC}"

# Delete database release
curl -s -X DELETE "$BASE_URL/database-releases/$DB_RELEASE_ID" > /dev/null
echo -e "${GREEN}✓ Deleted database release${NC}"

# Delete study
curl -s -X DELETE "$BASE_URL/studies/$STUDY_ID" > /dev/null
echo -e "${GREEN}✓ Deleted study${NC}"

# Delete test user
curl -s -X DELETE "$BASE_URL/users/$USER_ID" > /dev/null
echo -e "${GREEN}✓ Deleted test user${NC}"

# FINAL RESULTS
echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}TEST RESULTS SUMMARY${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Tests Run: $TESTS_RUN"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    echo -e "${GREEN}The tracker DELETE endpoint is working correctly.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}Please review the failed tests above.${NC}"
    exit 1
fi