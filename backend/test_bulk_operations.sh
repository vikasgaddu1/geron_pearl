#!/bin/bash

# Test bulk operations for Reporting Effort Tracker
# Tests bulk TLF upload, bulk Dataset upload, and validation

BASE_URL="http://localhost:8000/api/v1"

echo "========================================"
echo "Testing Bulk Operations"
echo "========================================"
echo ""

# Setup: Create test reporting effort
echo "Setup: Creating test reporting effort..."
EFFORT_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-efforts/" \
  -H "Content-Type: application/json" \
  -d '{
    "study_id": 1,
    "database_release_id": 1,
    "reporting_effort_label": "Test Bulk Operations Effort",
    "description": "Test effort for bulk operations"
  }')

if echo "$EFFORT_RESPONSE" | grep -q '"id"'; then
  EFFORT_ID=$(echo "$EFFORT_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  echo "✓ Created test reporting effort with ID: $EFFORT_ID"
else
  echo "⚠ Could not create test reporting effort, using ID 1"
  EFFORT_ID=1
fi
echo ""

# Test 1: Bulk TLF Upload
echo "Test 1: Bulk TLF Upload (10 items)"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/bulk-tlf" \
  -H "Content-Type: application/json" \
  -d '[
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_BULK_001", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_BULK_002", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_BULK_001", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_BULK_002", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_BULK_001", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_BULK_002", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_BULK_003", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_BULK_003", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_BULK_003", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_BULK_004", "is_active": true}
    ]')

if echo "$RESPONSE" | grep -q '"created_count":10'; then
  echo "✓ Successfully created 10 TLF items"
  echo "  Response: $(echo "$RESPONSE" | grep -o '"created_count":[0-9]*')"
else
  echo "✗ Failed to create TLF items"
  echo "  Response: $RESPONSE"
fi
echo ""

# Test 2: Bulk Dataset Upload
echo "Test 2: Bulk Dataset Upload (5 items)"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/bulk-dataset" \
  -H "Content-Type: application/json" \
  -d '[
      {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "DS_SDTM_001", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "DS_SDTM_002", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "DS_ADAM_001", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "DS_ADAM_002", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "Analysis", "item_code": "DS_ANALYSIS_001", "is_active": true}
    ]')

if echo "$RESPONSE" | grep -q '"created_count":5'; then
  echo "✓ Successfully created 5 Dataset items"
  echo "  Response: $(echo "$RESPONSE" | grep -o '"created_count":[0-9]*')"
else
  echo "✗ Failed to create Dataset items"
  echo "  Response: $RESPONSE"
fi
echo ""

# Test 3: Duplicate detection
echo "Test 3: Testing duplicate detection"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/bulk-tlf" \
  -H "Content-Type: application/json" \
  -d '[
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_BULK_001", "is_active": true}
    ]')

if echo "$RESPONSE" | grep -q '"errors".*"duplicate"'; then
  echo "✓ Duplicate detection working correctly"
elif echo "$RESPONSE" | grep -q '"created_count":0'; then
  echo "✓ No duplicates created (count = 0)"
else
  echo "✗ Duplicate was created or unexpected response"
  echo "  Response: $RESPONSE"
fi
echo ""

# Test 4: Invalid data validation
echo "Test 4: Testing validation (invalid item_type)"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/bulk-tlf" \
  -H "Content-Type: application/json" \
  -d '[
      {"item_type": "INVALID", "item_subtype": "Table", "item_code": "T_INVALID_001", "is_active": true}
    ]')

if echo "$RESPONSE" | grep -q '"errors"'; then
  echo "✓ Validation correctly rejected invalid item_type"
elif echo "$RESPONSE" | grep -q '"detail"'; then
  echo "✓ Validation error returned"
else
  echo "✗ Invalid data was accepted"
  echo "  Response: $RESPONSE"
fi
echo ""

# Test 5: Large batch upload (100+ items)
echo "Test 5: Large batch upload (100 items)"
# Generate JSON for 100 items
ITEMS_JSON="["
for i in $(seq 1 100); do
  # Determine type cycling through Table, Figure, Listing
  if [ $((i % 3)) -eq 0 ]; then
    SUBTYPE="Table"
    PREFIX="T"
  elif [ $((i % 3)) -eq 1 ]; then
    SUBTYPE="Figure"
    PREFIX="F"
  else
    SUBTYPE="Listing"
    PREFIX="L"
  fi
  
  ITEMS_JSON="${ITEMS_JSON}{\"item_type\":\"TLF\",\"item_subtype\":\"${SUBTYPE}\",\"item_code\":\"${PREFIX}_LARGE_$(printf '%03d' $i)\",\"is_active\":true}"
  
  if [ $i -lt 100 ]; then
    ITEMS_JSON="${ITEMS_JSON},"
  fi
done
ITEMS_JSON="${ITEMS_JSON}]"

START_TIME=$(date +%s)
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/bulk-tlf" \
  -H "Content-Type: application/json" \
  -d "${ITEMS_JSON}")
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if echo "$RESPONSE" | grep -q '"created_count":100'; then
  echo "✓ Successfully created 100 items in ${DURATION} seconds"
  echo "  Response: $(echo "$RESPONSE" | grep -o '"created_count":[0-9]*')"
elif echo "$RESPONSE" | grep -q '"created_count":[0-9]*'; then
  COUNT=$(echo "$RESPONSE" | grep -o '"created_count":[0-9]*' | grep -o '[0-9]*')
  echo "⚠ Created ${COUNT} out of 100 items in ${DURATION} seconds"
  echo "  Some may have been duplicates"
else
  echo "✗ Failed large batch upload"
  echo "  Response: $RESPONSE"
fi
echo ""

# Test 6: Copy from package
echo "Test 6: Testing copy from package functionality"
# First check if we have packages
PACKAGES=$(curl -s -X GET "$BASE_URL/packages?limit=1")
if echo "$PACKAGES" | grep -q '"id"'; then
  PACKAGE_ID=$(echo "$PACKAGES" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  echo "Using package ID: $PACKAGE_ID"
  
  RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/copy-from-package" \
    -H "Content-Type: application/json" \
    -d "{
      \"package_id\": $PACKAGE_ID
    }")
  
  if echo "$RESPONSE" | grep -q '"created_count"'; then
    COUNT=$(echo "$RESPONSE" | grep -o '"created_count":[0-9]*' | grep -o '[0-9]*')
    echo "✓ Successfully copied $COUNT items from package"
  else
    echo "✗ Failed to copy from package"
    echo "  Response: $RESPONSE"
  fi
else
  echo "⚠ No packages available to test copy functionality"
fi
echo ""

# Test 7: Copy from reporting effort
echo "Test 7: Testing copy from reporting effort functionality"
# First check if we have other reporting efforts
EFFORTS=$(curl -s -X GET "$BASE_URL/reporting-efforts?limit=2")
if echo "$EFFORTS" | grep -q '"id"'; then
  # Try to get a different effort ID (not 1)
  EFFORT_IDS=$(echo "$EFFORTS" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
  SOURCE_EFFORT_ID=""
  for ID in $EFFORT_IDS; do
    if [ "$ID" != "1" ]; then
      SOURCE_EFFORT_ID=$ID
      break
    fi
  done
  
  if [ -n "$SOURCE_EFFORT_ID" ]; then
    echo "Using source reporting effort ID: $SOURCE_EFFORT_ID"
    
    RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/copy-from-reporting-effort" \
      -H "Content-Type: application/json" \
      -d "{
        \"source_reporting_effort_id\": $SOURCE_EFFORT_ID
      }")
    
    if echo "$RESPONSE" | grep -q '"created_count"'; then
      COUNT=$(echo "$RESPONSE" | grep -o '"created_count":[0-9]*' | grep -o '[0-9]*')
      echo "✓ Successfully copied $COUNT items from reporting effort"
    else
      echo "✗ Failed to copy from reporting effort"
      echo "  Response: $RESPONSE"
    fi
  else
    echo "⚠ No other reporting efforts available to test copy functionality"
  fi
else
  echo "⚠ No reporting efforts available to test copy functionality"
fi
echo ""

# Test 8: Verify tracker auto-creation
echo "Test 8: Verifying tracker auto-creation for bulk items"
# Get one of the created items
RESPONSE=$(curl -s -X GET "$BASE_URL/reporting-effort-items?limit=1&skip=0")
if echo "$RESPONSE" | grep -q '"id"'; then
  ITEM_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  echo "Checking tracker for item ID: $ITEM_ID"
  
  TRACKER_RESPONSE=$(curl -s -X GET "$BASE_URL/reporting-effort-trackers/by-item/$ITEM_ID")
  
  if echo "$TRACKER_RESPONSE" | grep -q '"reporting_effort_item_id":'$ITEM_ID; then
    echo "✓ Tracker was auto-created for bulk uploaded item"
    
    # Check default values
    if echo "$TRACKER_RESPONSE" | grep -q '"production_status":"not_started"'; then
      echo "✓ Default production_status is 'not_started'"
    fi
    
    if echo "$TRACKER_RESPONSE" | grep -q '"priority":"medium"'; then
      echo "✓ Default priority is 'medium'"
    fi
    
    if echo "$TRACKER_RESPONSE" | grep -q '"qc_status":"not_started"'; then
      echo "✓ Default qc_status is 'not_started'"
    fi
  else
    echo "✗ Tracker was not created for bulk uploaded item"
    echo "  Response: $TRACKER_RESPONSE"
  fi
else
  echo "✗ Could not retrieve any items to check tracker creation"
fi
echo ""

# Test 9: Performance test with mixed operations
echo "Test 9: Mixed bulk operations test"
echo "Creating TLFs, Datasets, and checking performance..."

START_TIME=$(date +%s)

# Create 20 TLFs
TLF_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/bulk-tlf" \
  -H "Content-Type: application/json" \
  -d '[
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_MIXED_001", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_MIXED_002", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_MIXED_001", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_MIXED_002", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_MIXED_001", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_MIXED_002", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_MIXED_003", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_MIXED_003", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_MIXED_003", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_MIXED_004", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_MIXED_005", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_MIXED_004", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_MIXED_005", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_MIXED_004", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_MIXED_005", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_MIXED_006", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_MIXED_006", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Listing", "item_code": "L_MIXED_006", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Table", "item_code": "T_MIXED_007", "is_active": true},
      {"item_type": "TLF", "item_subtype": "Figure", "item_code": "F_MIXED_007", "is_active": true}
    ]')

# Create 10 Datasets
DS_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/$EFFORT_ID/bulk-dataset" \
  -H "Content-Type: application/json" \
  -d '[
      {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "DS_MIXED_SDTM_001", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "DS_MIXED_SDTM_002", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "DS_MIXED_ADAM_001", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "DS_MIXED_ADAM_002", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "Analysis", "item_code": "DS_MIXED_ANALYSIS_001", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "DS_MIXED_SDTM_003", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "DS_MIXED_ADAM_003", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "Analysis", "item_code": "DS_MIXED_ANALYSIS_002", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "SDTM", "item_code": "DS_MIXED_SDTM_004", "is_active": true},
      {"item_type": "Dataset", "item_subtype": "ADaM", "item_code": "DS_MIXED_ADAM_004", "is_active": true}
    ]')

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

TLF_COUNT=$(echo "$TLF_RESPONSE" | grep -o '"created_count":[0-9]*' | grep -o '[0-9]*')
DS_COUNT=$(echo "$DS_RESPONSE" | grep -o '"created_count":[0-9]*' | grep -o '[0-9]*')
TOTAL_COUNT=$((TLF_COUNT + DS_COUNT))

echo "✓ Mixed bulk operations completed in ${DURATION} seconds"
echo "  Created ${TLF_COUNT} TLFs and ${DS_COUNT} Datasets (Total: ${TOTAL_COUNT})"
echo ""

# Cleanup message
echo "========================================"
echo "Bulk Operations Testing Complete"
echo "========================================"
echo ""
echo "Note: Test data has been created in the database."
echo "To clean up test data, you may want to delete items with codes containing:"
echo "  - BULK_"
echo "  - LARGE_"
echo "  - MIXED_"
echo ""