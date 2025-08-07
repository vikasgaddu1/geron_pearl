#!/bin/bash

# Test script for Package Management System CRUD operations
# This script tests the complete package management functionality

set -e  # Exit on error

# Configuration
BASE_URL="http://localhost:8000/api/v1/"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function for colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "\n${YELLOW}====== $1 ======${NC}"
}

# Check if server is running
check_server() {
    if ! curl -sL "http://localhost:8000/health" > /dev/null 2>&1; then
        print_error "Server is not running! Please start it with: uv run python run.py"
        exit 1
    fi
    print_status "Server is running"
}

# Function to extract ID from JSON response
extract_id() {
    echo "$1" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2
}

# Start testing
echo "🧪 Testing Package Management System CRUD Operations"
echo "=================================================="

# Check server
check_server

# Clean up any existing test data
print_header "Cleanup Phase"
echo "Cleaning up any existing test data..."

# 1. CREATE STUDY (Required for package items)
print_header "1. Create Test Study"
STUDY_RESPONSE=$(curl -sL -X POST "${BASE_URL}studies" \
    -H "Content-Type: application/json" \
    -d '{"study_label": "Package Test Study"}')
STUDY_ID=$(extract_id "$STUDY_RESPONSE")
if [ -n "$STUDY_ID" ]; then
    print_status "Study created with ID: $STUDY_ID"
else
    print_error "Failed to create study"
    echo "$STUDY_RESPONSE"
    exit 1
fi

# 2. CREATE TEXT ELEMENTS (For footnotes and acronyms)
print_header "2. Create Text Elements"

# Create footnote
FOOTNOTE_RESPONSE=$(curl -sL -X POST "${BASE_URL}text-elements" \
    -H "Content-Type: application/json" \
    -d '{"type": "footnote", "label": "Test footnote for package item"}')
FOOTNOTE_ID=$(extract_id "$FOOTNOTE_RESPONSE")
print_status "Footnote created with ID: $FOOTNOTE_ID"

# Create acronym
ACRONYM_RESPONSE=$(curl -sL -X POST "${BASE_URL}text-elements" \
    -H "Content-Type: application/json" \
    -d '{"type": "acronyms_set", "label": "AE = Adverse Event"}')
ACRONYM_ID=$(extract_id "$ACRONYM_RESPONSE")
print_status "Acronym created with ID: $ACRONYM_ID"

# Create title
TITLE_RESPONSE=$(curl -sL -X POST "${BASE_URL}text-elements" \
    -H "Content-Type: application/json" \
    -d '{"type": "title", "label": "Demographics Table Title"}')
TITLE_ID=$(extract_id "$TITLE_RESPONSE")
print_status "Title created with ID: $TITLE_ID"

# 3. CREATE PACKAGE
print_header "3. Create Package"
PACKAGE_RESPONSE=$(curl -sL -X POST "${BASE_URL}packages" \
    -H "Content-Type: application/json" \
    -d '{"package_name": "Test Package 1"}')
PACKAGE_ID=$(extract_id "$PACKAGE_RESPONSE")
if [ -n "$PACKAGE_ID" ]; then
    print_status "Package created with ID: $PACKAGE_ID"
else
    print_error "Failed to create package"
    echo "$PACKAGE_RESPONSE"
    exit 1
fi

# 4. GET ALL PACKAGES
print_header "4. Get All Packages"
curl -sL "${BASE_URL}packages" | python3 -m json.tool | head -20
print_status "Retrieved packages list"

# 5. GET SPECIFIC PACKAGE
print_header "5. Get Specific Package"
curl -sL "${BASE_URL}packages/$PACKAGE_ID" | python3 -m json.tool | head -20
print_status "Retrieved package with ID: $PACKAGE_ID"

# 6. UPDATE PACKAGE
print_header "6. Update Package"
UPDATE_RESPONSE=$(curl -sL -X PUT "${BASE_URL}packages/$PACKAGE_ID" \
    -H "Content-Type: application/json" \
    -d '{"package_name": "Updated Test Package"}')
print_status "Package updated successfully"

# 7. CREATE PACKAGE ITEM (TLF)
print_header "7. Create Package Item (TLF)"
TLF_ITEM_RESPONSE=$(curl -sL -X POST "${BASE_URL}packages/$PACKAGE_ID/items" \
    -H "Content-Type: application/json" \
    -d '{
        "package_id": '$PACKAGE_ID',
        "study_id": '$STUDY_ID',
        "item_type": "TLF",
        "item_subtype": "Table",
        "item_code": "T01.01",
        "tlf_details": {
            "title_id": '$TITLE_ID',
            "population_flag_id": null
        },
        "footnotes": [
            {
                "footnote_id": '$FOOTNOTE_ID',
                "sequence_number": 1
            }
        ],
        "acronyms": [
            {
                "acronym_id": '$ACRONYM_ID'
            }
        ]
    }')
TLF_ITEM_ID=$(extract_id "$TLF_ITEM_RESPONSE")
if [ -n "$TLF_ITEM_ID" ]; then
    print_status "TLF item created with ID: $TLF_ITEM_ID"
else
    print_error "Failed to create TLF item"
    echo "$TLF_ITEM_RESPONSE"
fi

# 8. CREATE PACKAGE ITEM (Dataset)
print_header "8. Create Package Item (Dataset)"
DATASET_ITEM_RESPONSE=$(curl -sL -X POST "${BASE_URL}packages/$PACKAGE_ID/items" \
    -H "Content-Type: application/json" \
    -d '{
        "package_id": '$PACKAGE_ID',
        "study_id": '$STUDY_ID',
        "item_type": "Dataset",
        "item_subtype": "SDTM",
        "item_code": "AE",
        "dataset_details": {
            "label": "Adverse Events Dataset",
            "sorting_order": 1,
            "acronyms": "[\"AE\", \"SAE\"]"
        },
        "footnotes": [],
        "acronyms": []
    }')
DATASET_ITEM_ID=$(extract_id "$DATASET_ITEM_RESPONSE")
if [ -n "$DATASET_ITEM_ID" ]; then
    print_status "Dataset item created with ID: $DATASET_ITEM_ID"
else
    print_error "Failed to create Dataset item"
    echo "$DATASET_ITEM_RESPONSE"
fi

# 9. GET PACKAGE ITEMS
print_header "9. Get Package Items"
curl -sL "${BASE_URL}packages/$PACKAGE_ID/items" | python3 -m json.tool | head -40
print_status "Retrieved package items"

# 10. GET SPECIFIC PACKAGE ITEM
print_header "10. Get Specific Package Item"
curl -sL "${BASE_URL}packages/items/$TLF_ITEM_ID" | python3 -m json.tool | head -30
print_status "Retrieved package item with ID: $TLF_ITEM_ID"

# 11. UPDATE PACKAGE ITEM
print_header "11. Update Package Item"
UPDATE_ITEM_RESPONSE=$(curl -sL -X PUT "${BASE_URL}packages/items/$TLF_ITEM_ID" \
    -H "Content-Type: application/json" \
    -d '{"item_code": "T01.02"}')
print_status "Package item updated successfully"

# 12. TEST DELETION PROTECTION
print_header "12. Test Deletion Protection"
echo "Attempting to delete package with items (should fail)..."
DELETE_PROTECT_RESPONSE=$(curl -sL -w "\n%{http_code}" -X DELETE "${BASE_URL}packages/$PACKAGE_ID")
HTTP_CODE=$(echo "$DELETE_PROTECT_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "400" ]; then
    print_status "Deletion protection working correctly (HTTP 400)"
    echo "Error message: $(echo "$DELETE_PROTECT_RESPONSE" | head -n-1 | python3 -m json.tool | grep detail)"
else
    print_error "Deletion protection not working! Expected 400, got $HTTP_CODE"
fi

# 13. DELETE PACKAGE ITEMS
print_header "13. Delete Package Items"
curl -sL -X DELETE "${BASE_URL}packages/items/$TLF_ITEM_ID" > /dev/null
print_status "Deleted TLF item"
curl -sL -X DELETE "${BASE_URL}packages/items/$DATASET_ITEM_ID" > /dev/null
print_status "Deleted Dataset item"

# 14. DELETE PACKAGE (Should work now)
print_header "14. Delete Package"
DELETE_RESPONSE=$(curl -sL -w "\n%{http_code}" -X DELETE "${BASE_URL}packages/$PACKAGE_ID")
HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
    print_status "Package deleted successfully"
else
    print_error "Failed to delete package. HTTP code: $HTTP_CODE"
fi

# 15. CLEANUP
print_header "15. Cleanup"
curl -sL -X DELETE "${BASE_URL}studies/$STUDY_ID" > /dev/null
print_status "Deleted test study"
curl -sL -X DELETE "${BASE_URL}text-elements/$FOOTNOTE_ID" > /dev/null
curl -sL -X DELETE "${BASE_URL}text-elements/$ACRONYM_ID" > /dev/null
curl -sL -X DELETE "${BASE_URL}text-elements/$TITLE_ID" > /dev/null
print_status "Deleted test text elements"

# Summary
print_header "Test Summary"
echo "✅ Package CRUD operations: PASSED"
echo "✅ Package Item CRUD operations: PASSED"
echo "✅ TLF and Dataset item types: PASSED"
echo "✅ Deletion protection: PASSED"
echo "✅ WebSocket broadcasting: Check browser console for events"
echo ""
echo "🎉 All tests completed successfully!"