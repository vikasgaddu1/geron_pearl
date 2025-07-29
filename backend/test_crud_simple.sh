#!/bin/bash

# Simple CRUD Testing Script for PEARL Backend
# Tests all endpoints using curl commands and validates expected results

# Note: Strict error handling disabled to allow graceful test failure handling

# Configuration
BASE_URL="http://localhost:8000"
API_BASE="${BASE_URL}/api/v1/studies"
TIMESTAMP=$(date +%s)
TEST_LABEL="test-study-${TIMESTAMP}"
UPDATED_LABEL="test-study-updated-${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
CREATED_IDS=()

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

test_endpoint() {
    local test_name="$1"
    local expected_status="$2"
    local response_file="$3"
    local actual_status="$4"
    
    ((TOTAL_TESTS++))
    
    if [ "$expected_status" -eq "$actual_status" ]; then
        log_success "$test_name - Status: $actual_status"
        return 0
    else
        log_error "$test_name - Expected: $expected_status, Got: $actual_status"
        return 1
    fi
}

cleanup_test_data() {
    log_info "Cleaning up test data..."
    for id in "${CREATED_IDS[@]}"; do
        if [ -n "$id" ]; then
            log_info "Deleting study ID: $id"
            curl -s -X DELETE "${API_BASE}/${id}" -w "%{http_code}" -o /dev/null || true
        fi
    done
}

# Trap to ensure cleanup runs even if script fails
trap cleanup_test_data EXIT

echo "============================================"
echo "      PEARL Backend Simple CRUD Tests      "
echo "============================================"
echo "Base URL: $BASE_URL"
echo "Test Label: $TEST_LABEL"
echo "Timestamp: $TIMESTAMP"
echo "============================================"

# Check if server is running
log_info "Checking if server is running..."
if ! curl -s "$BASE_URL/health" > /dev/null; then
    log_error "Server is not running at $BASE_URL"
    log_info "Please start the server with: cd /mnt/c/python/PEARL/backend && uv run uvicorn app.main:app --reload"
    exit 1
fi
log_success "Server is running"

# 1. Health Check
log_info "Testing health endpoint..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" "$BASE_URL/health")
test_endpoint "Health Check" 200 "$response" "$status"
rm "$response"

# 2. CREATE - Post a new study
log_info "Testing CREATE endpoint..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" -X POST "$API_BASE/" \
    -H "Content-Type: application/json" \
    -d "{\"study_label\": \"$TEST_LABEL\"}")

if test_endpoint "CREATE Study" 201 "$response" "$status"; then
    # Extract the created study ID
    CREATED_ID=$(cat "$response" | grep -o '"id":[0-9]*' | cut -d: -f2)
    if [ -n "$CREATED_ID" ]; then
        CREATED_IDS+=("$CREATED_ID")
        log_info "Created study with ID: $CREATED_ID"
    else
        log_error "Failed to extract study ID from response"
    fi
else
    log_info "Response: $(cat "$response")"
fi
rm "$response"

# 3. READ ALL - Get all studies
log_info "Testing READ ALL endpoint..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" "$API_BASE/")
test_endpoint "READ ALL Studies" 200 "$response" "$status"

# Check if our created study is in the list
if [ -n "$CREATED_ID" ]; then
    if grep -q "\"id\":$CREATED_ID" "$response"; then
        log_success "Created study found in studies list"
        ((PASSED_TESTS++))
    else
        log_error "Created study not found in studies list"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
fi
rm "$response"

# 4. READ ONE - Get specific study by ID
if [ -n "$CREATED_ID" ]; then
    log_info "Testing READ ONE endpoint..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" "$API_BASE/$CREATED_ID")
    
    if test_endpoint "READ ONE Study" 200 "$response" "$status"; then
        # Verify the response contains the correct label
        if grep -q "\"study_label\":\"$TEST_LABEL\"" "$response"; then
            log_success "Study label matches expected value"
            ((PASSED_TESTS++))
        else
            log_error "Study label does not match expected value"
            log_info "Response: $(cat "$response")"
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    fi
    rm "$response"
fi

# 5. UPDATE - Update the study
if [ -n "$CREATED_ID" ]; then
    log_info "Testing UPDATE endpoint..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" -X PUT "$API_BASE/$CREATED_ID" \
        -H "Content-Type: application/json" \
        -d "{\"study_label\": \"$UPDATED_LABEL\"}")
    
    if test_endpoint "UPDATE Study" 200 "$response" "$status"; then
        # Verify the response contains the updated label
        if grep -q "\"study_label\":\"$UPDATED_LABEL\"" "$response"; then
            log_success "Study updated successfully with new label"
            ((PASSED_TESTS++))
        else
            log_error "Study update did not reflect new label"
            log_info "Response: $(cat "$response")"
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    fi
    rm "$response"
fi

# 6. READ ONE UPDATED - Verify update persisted
if [ -n "$CREATED_ID" ]; then
    log_info "Testing READ after UPDATE..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" "$API_BASE/$CREATED_ID")
    
    if test_endpoint "READ Updated Study" 200 "$response" "$status"; then
        # Verify the response contains the updated label
        if grep -q "\"study_label\":\"$UPDATED_LABEL\"" "$response"; then
            log_success "Updated study label persisted correctly"
            ((PASSED_TESTS++))
        else
            log_error "Updated study label did not persist"
            log_info "Response: $(cat "$response")"
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    fi
    rm "$response"
fi

# 7. DELETE - Delete the study
if [ -n "$CREATED_ID" ]; then
    log_info "Testing DELETE endpoint..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" -X DELETE "$API_BASE/$CREATED_ID")
    test_endpoint "DELETE Study" 200 "$response" "$status"
    rm "$response"
    
    # Remove from cleanup list since we just deleted it
    CREATED_IDS=("${CREATED_IDS[@]/$CREATED_ID}")
fi

# 8. READ DELETED - Verify study is gone
if [ -n "$CREATED_ID" ]; then
    log_info "Testing READ deleted study (should return 404)..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" "$API_BASE/$CREATED_ID")
    test_endpoint "READ Deleted Study (404 expected)" 404 "$response" "$status"
    rm "$response"
fi

# 9. CREATE Duplicate Label Test
log_info "Testing duplicate label prevention..."
response=$(mktemp)
# First create a study
status1=$(curl -s -w "%{http_code}" -o "$response" -X POST "$API_BASE/" \
    -H "Content-Type: application/json" \
    -d "{\"study_label\": \"duplicate-test-$TIMESTAMP\"}")

if [ "$status1" -eq 201 ]; then
    # Extract ID for cleanup
    DUPLICATE_ID=$(cat "$response" | grep -o '"id":[0-9]*' | cut -d: -f2)
    if [ -n "$DUPLICATE_ID" ]; then
        CREATED_IDS+=("$DUPLICATE_ID")
    fi
    
    # Try to create another with same label
    status2=$(curl -s -w "%{http_code}" -o "$response" -X POST "$API_BASE/" \
        -H "Content-Type: application/json" \
        -d "{\"study_label\": \"duplicate-test-$TIMESTAMP\"}")
    
    test_endpoint "Duplicate Label Prevention" 400 "$response" "$status2"
else
    log_error "Failed to create first study for duplicate test"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
fi
rm "$response"

# 10. Test Invalid Data
log_info "Testing invalid data handling..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" -X POST "$API_BASE/" \
    -H "Content-Type: application/json" \
    -d "{\"study_label\": \"\"}")
test_endpoint "Empty Label Validation" 422 "$response" "$status"
rm "$response"

# Results Summary
echo "============================================"
echo "              Test Results                  "
echo "============================================"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed!${NC}"
    exit 1
fi