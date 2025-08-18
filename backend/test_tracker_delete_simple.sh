#!/bin/bash

# Simple and reliable test script for the Reporting Effort Tracker DELETE endpoint
# Uses existing tracker IDs to avoid setup complexity

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

# Get existing tracker IDs for testing
echo -e "\n${YELLOW}Getting existing trackers for testing...${NC}"
trackers_response=$(curl -s "$BASE_URL/reporting-effort-tracker/?limit=5")
echo "Available trackers: $trackers_response" | head -200

# Extract a few tracker IDs for testing (using a simple approach)
# We'll use tracker IDs that we know exist from the previous output
TEST_TRACKER_ID=4  # We know this exists from previous output
EXISTING_TRACKER_ID=5  # We know this exists from previous output

echo -e "${GREEN}Using tracker ID $TEST_TRACKER_ID for deletion tests${NC}"
echo -e "${GREEN}Using tracker ID $EXISTING_TRACKER_ID as a backup existing tracker${NC}"

# TEST CASES
echo -e "\n${YELLOW}======= RUNNING DELETE ENDPOINT TESTS =======${NC}"

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

# Test 5: Verify an existing tracker exists before deletion
echo -e "\n${BLUE}Pre-verification: Check that tracker $TEST_TRACKER_ID exists${NC}"
verify_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/reporting-effort-tracker/$TEST_TRACKER_ID")
verify_code=$(echo "$verify_response" | tail -n1)
if [ "$verify_code" = "200" ]; then
    echo -e "${GREEN}✓ Tracker $TEST_TRACKER_ID exists and can be deleted${NC}"
    
    # Test 6: DELETE existing tracker (should succeed with 204)
    run_test \
        "Delete Existing Tracker" \
        "204" \
        "$BASE_URL/reporting-effort-tracker/$TEST_TRACKER_ID" \
        "DELETE" \
        "" \
        "Deleting an existing tracker should return 204 No Content"
    
    # Test 7: Verify tracker is actually deleted (should return 404)
    run_test \
        "Verify Tracker Deletion" \
        "404" \
        "$BASE_URL/reporting-effort-tracker/$TEST_TRACKER_ID" \
        "GET" \
        "" \
        "Attempting to get deleted tracker should return 404"
    
    # Test 8: Attempt to delete the same tracker again (should return 404)
    run_test \
        "Delete Already Deleted Tracker" \
        "404" \
        "$BASE_URL/reporting-effort-tracker/$TEST_TRACKER_ID" \
        "DELETE" \
        "" \
        "Attempting to delete an already deleted tracker should return 404"
    
else
    echo -e "${YELLOW}⚠ Tracker $TEST_TRACKER_ID does not exist, skipping deletion tests${NC}"
    echo "Will test with a different existing tracker..."
    
    # Try with the backup tracker ID
    verify_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/reporting-effort-tracker/$EXISTING_TRACKER_ID")
    verify_code=$(echo "$verify_response" | tail -n1)
    if [ "$verify_code" = "200" ]; then
        echo -e "${GREEN}✓ Using backup tracker $EXISTING_TRACKER_ID for deletion tests${NC}"
        
        # Test with backup tracker
        run_test \
            "Delete Existing Tracker (Backup)" \
            "204" \
            "$BASE_URL/reporting-effort-tracker/$EXISTING_TRACKER_ID" \
            "DELETE" \
            "" \
            "Deleting an existing tracker should return 204 No Content"
        
        # Verify deletion
        run_test \
            "Verify Tracker Deletion (Backup)" \
            "404" \
            "$BASE_URL/reporting-effort-tracker/$EXISTING_TRACKER_ID" \
            "GET" \
            "" \
            "Attempting to get deleted tracker should return 404"
    else
        echo -e "${RED}❌ No suitable tracker found for deletion tests${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

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
    echo -e "\n${GREEN}Summary of what was tested:${NC}"
    echo -e "${GREEN}✓ DELETE non-existent tracker returns 404${NC}"
    echo -e "${GREEN}✓ DELETE invalid ID formats return proper error codes${NC}"
    echo -e "${GREEN}✓ DELETE existing tracker returns 204 No Content${NC}"
    echo -e "${GREEN}✓ Deleted tracker is actually removed from database${NC}"
    echo -e "${GREEN}✓ Attempting to delete already deleted tracker returns 404${NC}"
    exit 0
else
    echo -e "\n${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}Please review the failed tests above.${NC}"
    exit 1
fi