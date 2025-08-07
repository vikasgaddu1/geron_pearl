#!/bin/bash

# Test script for packages frontend functionality

API_BASE="http://localhost:8000/api/v1"

echo "==========================================="
echo "Testing Packages Frontend Integration"
echo "==========================================="
echo ""

# Test 1: Get all packages
echo "1. Getting all packages..."
curl -s -X GET "$API_BASE/packages/" | jq '.' || echo "Error getting packages"
echo ""

# Test 2: Create a test package
echo "2. Creating test package..."
TEST_PACKAGE=$(curl -s -X POST "$API_BASE/packages/" \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "Test Package Frontend"
  }')

PACKAGE_ID=$(echo $TEST_PACKAGE | jq -r '.id')
echo "Created package with ID: $PACKAGE_ID"
echo ""

# Test 3: Get studies to use for items
echo "3. Getting available studies..."
STUDIES=$(curl -s -X GET "$API_BASE/studies/" | jq '.')
FIRST_STUDY_ID=$(echo $STUDIES | jq -r '.[0].id // empty')

if [ -z "$FIRST_STUDY_ID" ]; then
  echo "No studies available. Creating a test study..."
  TEST_STUDY=$(curl -s -X POST "$API_BASE/studies/" \
    -H "Content-Type: application/json" \
    -d '{
      "study_label": "Test Study for Packages"
    }')
  FIRST_STUDY_ID=$(echo $TEST_STUDY | jq -r '.id')
  echo "Created study with ID: $FIRST_STUDY_ID"
fi
echo ""

# Test 4: Create a TLF item
echo "4. Creating TLF item..."
curl -s -X POST "$API_BASE/packages/$PACKAGE_ID/items" \
  -H "Content-Type: application/json" \
  -d "{
    \"package_id\": $PACKAGE_ID,
    \"study_id\": $FIRST_STUDY_ID,
    \"item_type\": \"TLF\",
    \"item_subtype\": \"Table\",
    \"item_code\": \"T14.1.1\"
  }" | jq '.'
echo ""

# Test 5: Create a Dataset item
echo "5. Creating Dataset item..."
curl -s -X POST "$API_BASE/packages/$PACKAGE_ID/items" \
  -H "Content-Type: application/json" \
  -d "{
    \"package_id\": $PACKAGE_ID,
    \"study_id\": $FIRST_STUDY_ID,
    \"item_type\": \"Dataset\",
    \"item_subtype\": \"ADaM\",
    \"item_code\": \"ADSL\",
    \"dataset_details\": {
      \"label\": \"Subject-Level Analysis Dataset\"
    }
  }" | jq '.'
echo ""

# Test 6: Get package items
echo "6. Getting package items..."
curl -s -X GET "$API_BASE/packages/$PACKAGE_ID/items" | jq '.'
echo ""

echo "==========================================="
echo "Test complete! Check the frontend to see:"
echo "1. New package in the Packages tab"
echo "2. Package items in the Package Items tab"
echo "3. Real-time WebSocket updates"
echo "==========================================="