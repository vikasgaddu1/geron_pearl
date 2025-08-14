#!/bin/bash

# Simple CRUD Testing Script for PEARL Backend - Database Releases
# Tests all database release endpoints using curl commands and validates expected results

# Note: Strict error handling disabled to allow graceful test failure handling

# Configuration
BASE_URL="http://localhost:8000"
STUDIES_API="${BASE_URL}/api/v1/studies"
DB_RELEASES_API="${BASE_URL}/api/v1/database-releases"
TIMESTAMP=$(date +%s)
TEST_STUDY_LABEL="test-study-${TIMESTAMP}"
TEST_DB_RELEASE_LABEL="test-db-release-${TIMESTAMP}"
UPDATED_DB_RELEASE_LABEL="test-db-release-updated-${TIMESTAMP}"

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
CREATED_STUDY_IDS=()
CREATED_DB_RELEASE_IDS=()

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
    # Clean up database releases first (due to foreign key constraint)
    for id in "${CREATED_DB_RELEASE_IDS[@]}"; do
        if [ -n "$id" ]; then
            log_info "Deleting database release ID: $id"
            curl -s -X DELETE "${DB_RELEASES_API}/${id}" -w "%{http_code}" -o /dev/null || true
        fi
    done
    # Then clean up studies
    for id in "${CREATED_STUDY_IDS[@]}"; do
        if [ -n "$id" ]; then
            log_info "Deleting study ID: $id"
            curl -s -X DELETE "${STUDIES_API}/${id}" -w "%{http_code}" -o /dev/null || true
        fi
    done
}

# Trap to ensure cleanup runs even if script fails
trap cleanup_test_data EXIT

echo "============================================"
echo "   PEARL Backend Database Releases Tests   "
echo "============================================"
echo "Base URL: $BASE_URL"
echo "Test Study Label: $TEST_STUDY_LABEL"
echo "Test DB Release Label: $TEST_DB_RELEASE_LABEL"
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

# 2. CREATE Test Study (needed for database releases)
log_info "Creating test study for database releases..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" -X POST "$STUDIES_API/" \
    -H "Content-Type: application/json" \
    -d "{\"study_label\": \"$TEST_STUDY_LABEL\"}")

if test_endpoint "CREATE Test Study" 201 "$response" "$status"; then
    # Extract the created study ID
    STUDY_ID=$(cat "$response" | grep -o '"id":[0-9]*' | cut -d: -f2)
    if [ -n "$STUDY_ID" ]; then
        CREATED_STUDY_IDS+=("$STUDY_ID")
        log_info "Created test study with ID: $STUDY_ID"
    else
        log_error "Failed to extract study ID from response"
        exit 1
    fi
else
    log_error "Failed to create test study - cannot proceed with database release tests"
    log_info "Response: $(cat "$response")"
    exit 1
fi
rm "$response"

# 3. CREATE Database Release
log_info "Testing CREATE database release endpoint..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" -X POST "$DB_RELEASES_API/" \
    -H "Content-Type: application/json" \
    -d "{\"study_id\": $STUDY_ID, \"database_release_label\": \"$TEST_DB_RELEASE_LABEL\"}")

if test_endpoint "CREATE Database Release" 201 "$response" "$status"; then
    # Extract the created database release ID
    DB_RELEASE_ID=$(cat "$response" | grep -o '"id":[0-9]*' | cut -d: -f2)
    if [ -n "$DB_RELEASE_ID" ]; then
        CREATED_DB_RELEASE_IDS+=("$DB_RELEASE_ID")
        log_info "Created database release with ID: $DB_RELEASE_ID"
    else
        log_error "Failed to extract database release ID from response"
    fi
else
    log_info "Response: $(cat "$response")"
fi
rm "$response"

# 4. READ ALL Database Releases
log_info "Testing READ ALL database releases endpoint..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" "$DB_RELEASES_API/")
test_endpoint "READ ALL Database Releases" 200 "$response" "$status"

# Check if our created database release is in the list
if [ -n "$DB_RELEASE_ID" ]; then
    if grep -q "\"id\":$DB_RELEASE_ID" "$response"; then
        log_success "Created database release found in list"
        ((PASSED_TESTS++))
    else
        log_error "Created database release not found in list"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
fi
rm "$response"

# 5. READ ALL Database Releases filtered by study_id
log_info "Testing READ ALL database releases filtered by study_id..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" "$DB_RELEASES_API/?study_id=$STUDY_ID")
test_endpoint "READ ALL Database Releases by Study" 200 "$response" "$status"

# Check if our created database release is in the filtered list
if [ -n "$DB_RELEASE_ID" ]; then
    if grep -q "\"id\":$DB_RELEASE_ID" "$response"; then
        log_success "Created database release found in filtered list"
        ((PASSED_TESTS++))
    else
        log_error "Created database release not found in filtered list"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
fi
rm "$response"

# 6. READ ONE Database Release by ID
if [ -n "$DB_RELEASE_ID" ]; then
    log_info "Testing READ ONE database release endpoint..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" "$DB_RELEASES_API/$DB_RELEASE_ID")
    
    if test_endpoint "READ ONE Database Release" 200 "$response" "$status"; then
        # Verify the response contains the correct label and study_id
        if grep -q "\"database_release_label\":\"$TEST_DB_RELEASE_LABEL\"" "$response" && \
           grep -q "\"study_id\":$STUDY_ID" "$response"; then
            log_success "Database release label and study_id match expected values"
            ((PASSED_TESTS++))
        else
            log_error "Database release data does not match expected values"
            log_info "Response: $(cat "$response")"
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    fi
    rm "$response"
fi

# 7. UPDATE Database Release
if [ -n "$DB_RELEASE_ID" ]; then
    log_info "Testing UPDATE database release endpoint..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" -X PUT "$DB_RELEASES_API/$DB_RELEASE_ID" \
        -H "Content-Type: application/json" \
        -d "{\"database_release_label\": \"$UPDATED_DB_RELEASE_LABEL\"}")
    
    if test_endpoint "UPDATE Database Release" 200 "$response" "$status"; then
        # Verify the response contains the updated label
        if grep -q "\"database_release_label\":\"$UPDATED_DB_RELEASE_LABEL\"" "$response"; then
            log_success "Database release updated successfully with new label"
            ((PASSED_TESTS++))
        else
            log_error "Database release update did not reflect new label"
            log_info "Response: $(cat "$response")"
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    fi
    rm "$response"
fi

# 8. READ ONE UPDATED Database Release - Verify update persisted
if [ -n "$DB_RELEASE_ID" ]; then
    log_info "Testing READ after UPDATE..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" "$DB_RELEASES_API/$DB_RELEASE_ID")
    
    if test_endpoint "READ Updated Database Release" 200 "$response" "$status"; then
        # Verify the response contains the updated label
        if grep -q "\"database_release_label\":\"$UPDATED_DB_RELEASE_LABEL\"" "$response"; then
            log_success "Updated database release label persisted correctly"
            ((PASSED_TESTS++))
        else
            log_error "Updated database release label did not persist"
            log_info "Response: $(cat "$response")"
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    fi
    rm "$response"
fi

# 9. Test Foreign Key Constraint - Try to create database release with non-existent study_id
log_info "Testing foreign key constraint (non-existent study_id)..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" -X POST "$DB_RELEASES_API/" \
    -H "Content-Type: application/json" \
    -d "{\"study_id\": 999999, \"database_release_label\": \"test-fk-$TIMESTAMP\"}")
test_endpoint "Foreign Key Constraint Test" 404 "$response" "$status"
rm "$response"

# 10. Test Unique Constraint - Try to create duplicate database release label for same study
log_info "Testing unique constraint (duplicate label for same study)..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" -X POST "$DB_RELEASES_API/" \
    -H "Content-Type: application/json" \
    -d "{\"study_id\": $STUDY_ID, \"database_release_label\": \"$UPDATED_DB_RELEASE_LABEL\"}")
test_endpoint "Unique Constraint Test" 400 "$response" "$status"
rm "$response"

# 11. Test Invalid Data - Empty label
log_info "Testing invalid data handling (empty label)..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" -X POST "$DB_RELEASES_API/" \
    -H "Content-Type: application/json" \
    -d "{\"study_id\": $STUDY_ID, \"database_release_label\": \"\"}")
test_endpoint "Empty Label Validation" 422 "$response" "$status"
rm "$response"

# 12. Test Invalid Data - Missing study_id
log_info "Testing invalid data handling (missing study_id)..."
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" -X POST "$DB_RELEASES_API/" \
    -H "Content-Type: application/json" \
    -d "{\"database_release_label\": \"test-missing-study-$TIMESTAMP\"}")
test_endpoint "Missing Study ID Validation" 422 "$response" "$status"
rm "$response"

# 13. DELETE Database Release
if [ -n "$DB_RELEASE_ID" ]; then
    log_info "Testing DELETE database release endpoint..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" -X DELETE "$DB_RELEASES_API/$DB_RELEASE_ID")
    test_endpoint "DELETE Database Release" 200 "$response" "$status"
    rm "$response"
    
    # Remove from cleanup list since we just deleted it
    CREATED_DB_RELEASE_IDS=("${CREATED_DB_RELEASE_IDS[@]/$DB_RELEASE_ID}")
fi

# 14. READ DELETED Database Release - Verify it's gone
if [ -n "$DB_RELEASE_ID" ]; then
    log_info "Testing READ deleted database release (should return 404)..."
    response=$(mktemp)
    status=$(curl -s -w "%{http_code}" -o "$response" "$DB_RELEASES_API/$DB_RELEASE_ID")
    test_endpoint "READ Deleted Database Release (404 expected)" 404 "$response" "$status"
    rm "$response"
fi

# Results Summary
echo "============================================"
echo "              Test Results                  "
echo "============================================"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✅ All database release tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some database release tests failed!${NC}"
    exit 1
fi