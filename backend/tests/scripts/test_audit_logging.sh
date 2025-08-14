#!/bin/bash

# Test audit logging functionality
# Tests that CRUD operations are properly logged in the audit trail

BASE_URL="http://localhost:8000/api/v1"
ADMIN_HEADER="X-User-Role: admin"

echo "========================================"
echo "Testing Audit Logging Functionality"
echo "========================================"
echo ""

# Test 1: Create an item and check audit log
echo "Test 1: Creating an item and checking audit log"
# Create a reporting effort item
ITEM_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
  -H "Content-Type: application/json" \
  -d '{
    "reporting_effort_id": 1,
    "source_type": "custom",
    "item_type": "TLF",
    "item_subtype": "Table",
    "item_code": "T_AUDIT_TEST_001",
    "is_active": true
  }')

if echo "$ITEM_RESPONSE" | grep -q '"id"'; then
  ITEM_ID=$(echo "$ITEM_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  echo "✓ Created item with ID: $ITEM_ID"
  
  # Check audit log for CREATE action
  sleep 1  # Give time for audit log to be written
  AUDIT_RESPONSE=$(curl -s -X GET "$BASE_URL/audit-trail/?table_name=reporting_effort_items&action=CREATE&limit=5" \
    -H "$ADMIN_HEADER")
  
  if echo "$AUDIT_RESPONSE" | grep -q "T_AUDIT_TEST_001"; then
    echo "✓ CREATE action logged in audit trail"
  else
    echo "✗ CREATE action not found in audit trail"
    echo "  Response: $AUDIT_RESPONSE"
  fi
else
  echo "✗ Failed to create item"
  ITEM_ID=""
fi
echo ""

# Test 2: Update an item and check audit log
if [ -n "$ITEM_ID" ]; then
  echo "Test 2: Updating item and checking audit log"
  UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/reporting-effort-items/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -d '{
      "reporting_effort_id": 1,
      "source_type": "custom",
      "item_type": "TLF",
      "item_subtype": "Table",
      "item_code": "T_AUDIT_TEST_001_UPDATED",
      "is_active": true
    }')
  
  if echo "$UPDATE_RESPONSE" | grep -q '"item_code":"T_AUDIT_TEST_001_UPDATED"'; then
    echo "✓ Item updated successfully"
    
    # Check audit log for UPDATE action
    sleep 1
    AUDIT_RESPONSE=$(curl -s -X GET "$BASE_URL/audit-trail/?table_name=reporting_effort_items&action=UPDATE&limit=5" \
      -H "$ADMIN_HEADER")
    
    if echo "$AUDIT_RESPONSE" | grep -q "T_AUDIT_TEST_001_UPDATED"; then
      echo "✓ UPDATE action logged in audit trail"
    else
      echo "✗ UPDATE action not found in audit trail"
    fi
  else
    echo "✗ Failed to update item"
  fi
fi
echo ""

# Test 3: Delete an item and check audit log
if [ -n "$ITEM_ID" ]; then
  echo "Test 3: Deleting item and checking audit log"
  DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/reporting-effort-items/$ITEM_ID")
  
  if echo "$DELETE_RESPONSE" | grep -q '"message"'; then
    echo "✓ Item deleted successfully"
    
    # Check audit log for DELETE action
    sleep 1
    AUDIT_RESPONSE=$(curl -s -X GET "$BASE_URL/audit-trail/?table_name=reporting_effort_items&action=DELETE&limit=5" \
      -H "$ADMIN_HEADER")
    
    if echo "$AUDIT_RESPONSE" | grep -q "DELETE"; then
      echo "✓ DELETE action logged in audit trail"
    else
      echo "✗ DELETE action not found in audit trail"
    fi
  else
    echo "✗ Failed to delete item"
  fi
fi
echo ""

# Test 4: Test audit log filtering
echo "Test 4: Testing audit log filtering"

# Get all audit logs (admin only)
echo "Getting all recent audit logs..."
ALL_LOGS=$(curl -s -X GET "$BASE_URL/audit-trail/?limit=10" \
  -H "$ADMIN_HEADER")

if echo "$ALL_LOGS" | grep -q '\['; then
  echo "✓ Retrieved audit logs successfully"
  
  # Count entries
  LOG_COUNT=$(echo "$ALL_LOGS" | grep -o '"id"' | wc -l)
  echo "  Found $LOG_COUNT audit log entries"
else
  echo "✗ Failed to retrieve audit logs"
fi
echo ""

# Test 5: Test access control (non-admin should be denied)
echo "Test 5: Testing access control"
echo "Attempting to access audit logs without admin role..."
ACCESS_TEST=$(curl -s -X GET "$BASE_URL/audit-trail/?limit=5" \
  -H "X-User-Role: viewer")

if echo "$ACCESS_TEST" | grep -q '"detail".*"Admin access required"'; then
  echo "✓ Non-admin access correctly denied"
elif echo "$ACCESS_TEST" | grep -q '"detail".*"403"'; then
  echo "✓ Non-admin access correctly denied (403)"
else
  echo "✗ Security issue: Non-admin was able to access audit logs!"
  echo "  Response: $ACCESS_TEST"
fi
echo ""

# Test 6: Test filtering by date range
echo "Test 6: Testing date range filtering"
# Get logs from the last hour
CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S")
ONE_HOUR_AGO=$(date -u -d '1 hour ago' +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || date -u -v-1H +"%Y-%m-%dT%H:%M:%S")

DATE_FILTER_RESPONSE=$(curl -s -X GET "$BASE_URL/audit-trail/?start_date=${ONE_HOUR_AGO}&limit=10" \
  -H "$ADMIN_HEADER")

if echo "$DATE_FILTER_RESPONSE" | grep -q '\['; then
  echo "✓ Date filtering working"
  DATE_COUNT=$(echo "$DATE_FILTER_RESPONSE" | grep -o '"id"' | wc -l)
  echo "  Found $DATE_COUNT entries in the last hour"
else
  echo "✗ Date filtering failed"
fi
echo ""

# Test 7: Test changes_json field
echo "Test 7: Testing changes tracking"
# Create another item to test
TEST_ITEM_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
  -H "Content-Type: application/json" \
  -d '{
    "reporting_effort_id": 1,
    "source_type": "custom",
    "item_type": "Dataset",
    "item_subtype": "SDTM",
    "item_code": "DS_AUDIT_TEST",
    "is_active": true
  }')

if echo "$TEST_ITEM_RESPONSE" | grep -q '"id"'; then
  TEST_ITEM_ID=$(echo "$TEST_ITEM_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  
  # Update the item
  curl -s -X PUT "$BASE_URL/reporting-effort-items/$TEST_ITEM_ID" \
    -H "Content-Type: application/json" \
    -d '{
      "reporting_effort_id": 1,
      "source_type": "package",
      "source_id": 123,
      "item_type": "Dataset",
      "item_subtype": "ADaM",
      "item_code": "DS_AUDIT_TEST_MODIFIED",
      "is_active": false
    }' > /dev/null
  
  # Get audit log for this specific item
  sleep 1
  CHANGES_RESPONSE=$(curl -s -X GET "$BASE_URL/audit-trail/?table_name=reporting_effort_items&record_id=$TEST_ITEM_ID" \
    -H "$ADMIN_HEADER")
  
  if echo "$CHANGES_RESPONSE" | grep -q '"changes_json"'; then
    echo "✓ Changes are being tracked in audit log"
    
    # Check if both old and new values are captured
    if echo "$CHANGES_RESPONSE" | grep -q '"before"' && echo "$CHANGES_RESPONSE" | grep -q '"after"'; then
      echo "✓ Both before and after values are captured"
    else
      echo "⚠ Changes captured but before/after structure may be different"
    fi
  else
    echo "✗ Changes not tracked in audit log"
  fi
  
  # Clean up
  curl -s -X DELETE "$BASE_URL/reporting-effort-items/$TEST_ITEM_ID" > /dev/null
fi
echo ""

# Test 8: Test user tracking
echo "Test 8: Testing user tracking in audit log"
# Check if user information is captured
USER_TRACKING=$(curl -s -X GET "$BASE_URL/audit-trail/?limit=5" \
  -H "$ADMIN_HEADER")

if echo "$USER_TRACKING" | grep -q '"user_id"'; then
  echo "✓ User ID is tracked in audit log"
  
  if echo "$USER_TRACKING" | grep -q '"user_name"' || echo "$USER_TRACKING" | grep -q '"user_email"'; then
    echo "✓ User details are included in response"
  else
    echo "⚠ User ID tracked but details may not be populated"
  fi
else
  echo "✗ User tracking not implemented"
fi
echo ""

# Test 9: Performance test - retrieve large number of logs
echo "Test 9: Testing pagination and performance"
PERF_START=$(date +%s%N)
LARGE_RESPONSE=$(curl -s -X GET "$BASE_URL/audit-trail/?limit=500" \
  -H "$ADMIN_HEADER")
PERF_END=$(date +%s%N)
PERF_DURATION=$(( ($PERF_END - $PERF_START) / 1000000 ))

if echo "$LARGE_RESPONSE" | grep -q '\['; then
  LARGE_COUNT=$(echo "$LARGE_RESPONSE" | grep -o '"id"' | wc -l)
  echo "✓ Retrieved $LARGE_COUNT audit logs in ${PERF_DURATION}ms"
  
  if [ $PERF_DURATION -lt 5000 ]; then
    echo "✓ Good performance (under 5 seconds)"
  else
    echo "⚠ Slow performance (over 5 seconds)"
  fi
else
  echo "✗ Failed to retrieve large audit log set"
fi
echo ""

echo "========================================"
echo "Audit Logging Testing Complete"
echo "========================================"
echo ""
echo "Summary:"
echo "- Audit logging should capture all CRUD operations"
echo "- Access should be restricted to admin users only"
echo "- Filtering by table, user, action, and date should work"
echo "- Changes should be tracked with before/after values"
echo ""