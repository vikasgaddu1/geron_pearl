#!/bin/bash

# Test role-based permissions for Reporting Effort Tracker
# Tests different user roles (admin, editor, viewer) and their permissions

BASE_URL="http://localhost:8000/api/v1"
ADMIN_HEADER="X-User-Role: admin"
EDITOR_HEADER="X-User-Role: editor"
VIEWER_HEADER="X-User-Role: viewer"

echo "========================================"
echo "Testing Role-Based Permissions"
echo "========================================"
echo ""

# Test 1: Admin can create items
echo "Test 1: Admin creates reporting effort item"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
  -H "Content-Type: application/json" \
  -H "$ADMIN_HEADER" \
  -d '{
    "reporting_effort_id": 1,
    "source_type": "custom",
    "item_type": "TLF",
    "item_subtype": "Table",
    "item_code": "T_ROLE_TEST_ADMIN",
    "is_active": true
  }')

if echo "$RESPONSE" | grep -q '"id"'; then
  echo "✓ Admin can create items"
  ITEM_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
else
  echo "✗ Admin failed to create item: $RESPONSE"
  ITEM_ID=""
fi
echo ""

# Test 2: Editor can create items
echo "Test 2: Editor creates reporting effort item"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
  -H "Content-Type: application/json" \
  -H "$EDITOR_HEADER" \
  -d '{
    "reporting_effort_id": 1,
    "source_type": "custom",
    "item_type": "TLF",
    "item_subtype": "Figure",
    "item_code": "F_ROLE_TEST_EDITOR",
    "is_active": true
  }')

if echo "$RESPONSE" | grep -q '"id"'; then
  echo "✓ Editor can create items"
  EDITOR_ITEM_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
else
  echo "✗ Editor failed to create item: $RESPONSE"
  EDITOR_ITEM_ID=""
fi
echo ""

# Test 3: Viewer cannot create items (should fail)
echo "Test 3: Viewer attempts to create item (should fail)"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
  -H "Content-Type: application/json" \
  -H "$VIEWER_HEADER" \
  -d '{
    "reporting_effort_id": 1,
    "source_type": "custom",
    "item_type": "TLF",
    "item_subtype": "Listing",
    "item_code": "L_ROLE_TEST_VIEWER",
    "is_active": true
  }')

if echo "$RESPONSE" | grep -q '"detail".*"permission"'; then
  echo "✓ Viewer correctly denied creation permission"
elif echo "$RESPONSE" | grep -q '"id"'; then
  echo "✗ Security issue: Viewer was able to create item!"
else
  echo "? Unexpected response for viewer: $RESPONSE"
fi
echo ""

# Test 4: All roles can read items
echo "Test 4: Testing read permissions"
echo "Admin reading items:"
RESPONSE=$(curl -s -X GET "$BASE_URL/reporting-effort-items/" -H "$ADMIN_HEADER")
if echo "$RESPONSE" | grep -q '\['; then
  echo "✓ Admin can read items"
else
  echo "✗ Admin cannot read items"
fi

echo "Editor reading items:"
RESPONSE=$(curl -s -X GET "$BASE_URL/reporting-effort-items/" -H "$EDITOR_HEADER")
if echo "$RESPONSE" | grep -q '\['; then
  echo "✓ Editor can read items"
else
  echo "✗ Editor cannot read items"
fi

echo "Viewer reading items:"
RESPONSE=$(curl -s -X GET "$BASE_URL/reporting-effort-items/" -H "$VIEWER_HEADER")
if echo "$RESPONSE" | grep -q '\['; then
  echo "✓ Viewer can read items"
else
  echo "✗ Viewer cannot read items"
fi
echo ""

# Test 5: Update permissions
if [ -n "$ITEM_ID" ]; then
  echo "Test 5: Testing update permissions on item $ITEM_ID"
  
  echo "Admin updating item:"
  RESPONSE=$(curl -s -X PUT "$BASE_URL/reporting-effort-items/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -H "$ADMIN_HEADER" \
    -d '{
      "reporting_effort_id": 1,
      "source_type": "custom",
      "item_type": "TLF",
      "item_subtype": "Table",
      "item_code": "T_ROLE_TEST_ADMIN_UPDATED",
      "is_active": true
    }')
  
  if echo "$RESPONSE" | grep -q '"item_code":"T_ROLE_TEST_ADMIN_UPDATED"'; then
    echo "✓ Admin can update items"
  else
    echo "✗ Admin failed to update item"
  fi
  
  echo "Editor updating item:"
  RESPONSE=$(curl -s -X PUT "$BASE_URL/reporting-effort-items/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -H "$EDITOR_HEADER" \
    -d '{
      "reporting_effort_id": 1,
      "source_type": "custom",
      "item_type": "TLF",
      "item_subtype": "Table",
      "item_code": "T_ROLE_TEST_EDITOR_UPDATE",
      "is_active": true
    }')
  
  if echo "$RESPONSE" | grep -q '"item_code":"T_ROLE_TEST_EDITOR_UPDATE"'; then
    echo "✓ Editor can update items"
  else
    echo "✗ Editor failed to update item"
  fi
  
  echo "Viewer attempting update (should fail):"
  RESPONSE=$(curl -s -X PUT "$BASE_URL/reporting-effort-items/$ITEM_ID" \
    -H "Content-Type: application/json" \
    -H "$VIEWER_HEADER" \
    -d '{
      "reporting_effort_id": 1,
      "source_type": "custom",
      "item_type": "TLF",
      "item_subtype": "Table",
      "item_code": "T_ROLE_TEST_VIEWER_UPDATE",
      "is_active": true
    }')
  
  if echo "$RESPONSE" | grep -q '"detail".*"permission"'; then
    echo "✓ Viewer correctly denied update permission"
  elif echo "$RESPONSE" | grep -q '"item_code":"T_ROLE_TEST_VIEWER_UPDATE"'; then
    echo "✗ Security issue: Viewer was able to update item!"
  else
    echo "? Unexpected response for viewer update"
  fi
fi
echo ""

# Test 6: Comment permissions
echo "Test 6: Testing comment permissions"
if [ -n "$ITEM_ID" ]; then
  # Get tracker ID for the item
  RESPONSE=$(curl -s -X GET "$BASE_URL/reporting-effort-trackers/by-item/$ITEM_ID" -H "$ADMIN_HEADER")
  TRACKER_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  
  if [ -n "$TRACKER_ID" ]; then
    echo "Using tracker ID: $TRACKER_ID"
    
    # Admin creates programmer comment
    echo "Admin creating programmer comment:"
    RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-comments/" \
      -H "Content-Type: application/json" \
      -H "$ADMIN_HEADER" \
      -d "{
        \"tracker_id\": $TRACKER_ID,
        \"comment_text\": \"Admin programmer comment\",
        \"comment_type\": \"programmer_comment\",
        \"comment_category\": \"general\"
      }")
    
    if echo "$RESPONSE" | grep -q '"comment_type":"programmer_comment"'; then
      echo "✓ Admin can create programmer comments"
    else
      echo "✗ Admin failed to create programmer comment"
    fi
    
    # Editor creates programmer comment
    echo "Editor creating programmer comment:"
    RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-comments/" \
      -H "Content-Type: application/json" \
      -H "$EDITOR_HEADER" \
      -d "{
        \"tracker_id\": $TRACKER_ID,
        \"comment_text\": \"Editor programmer comment\",
        \"comment_type\": \"programmer_comment\",
        \"comment_category\": \"general\"
      }")
    
    if echo "$RESPONSE" | grep -q '"comment_type":"programmer_comment"'; then
      echo "✓ Editor can create programmer comments"
    else
      echo "✗ Editor failed to create programmer comment"
    fi
    
    # Viewer creates biostat comment (should work)
    echo "Viewer creating biostat comment:"
    RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-comments/" \
      -H "Content-Type: application/json" \
      -H "$VIEWER_HEADER" \
      -d "{
        \"tracker_id\": $TRACKER_ID,
        \"comment_text\": \"Viewer biostat comment\",
        \"comment_type\": \"biostat_comment\",
        \"comment_category\": \"general\"
      }")
    
    if echo "$RESPONSE" | grep -q '"comment_type":"biostat_comment"'; then
      echo "✓ Viewer can create biostat comments"
    else
      echo "✗ Viewer failed to create biostat comment"
    fi
    
    # Viewer attempts programmer comment (should fail)
    echo "Viewer attempting programmer comment (should fail):"
    RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-comments/" \
      -H "Content-Type: application/json" \
      -H "$VIEWER_HEADER" \
      -d "{
        \"tracker_id\": $TRACKER_ID,
        \"comment_text\": \"Viewer programmer comment attempt\",
        \"comment_type\": \"programmer_comment\",
        \"comment_category\": \"general\"
      }")
    
    if echo "$RESPONSE" | grep -q '"detail".*"permission"'; then
      echo "✓ Viewer correctly denied programmer comment permission"
    elif echo "$RESPONSE" | grep -q '"comment_type":"programmer_comment"'; then
      echo "✗ Security issue: Viewer was able to create programmer comment!"
    else
      echo "? Unexpected response for viewer programmer comment"
    fi
  else
    echo "✗ Could not get tracker ID"
  fi
fi
echo ""

# Test 7: Delete permissions
echo "Test 7: Testing delete permissions"
if [ -n "$EDITOR_ITEM_ID" ]; then
  echo "Viewer attempting delete (should fail):"
  RESPONSE=$(curl -s -X DELETE "$BASE_URL/reporting-effort-items/$EDITOR_ITEM_ID" -H "$VIEWER_HEADER")
  
  if echo "$RESPONSE" | grep -q '"detail".*"permission"'; then
    echo "✓ Viewer correctly denied delete permission"
  elif echo "$RESPONSE" | grep -q '"message".*"deleted"'; then
    echo "✗ Security issue: Viewer was able to delete item!"
  else
    echo "? Unexpected response for viewer delete"
  fi
  
  echo "Editor deleting own item:"
  RESPONSE=$(curl -s -X DELETE "$BASE_URL/reporting-effort-items/$EDITOR_ITEM_ID" -H "$EDITOR_HEADER")
  
  if echo "$RESPONSE" | grep -q '"message".*"deleted"'; then
    echo "✓ Editor can delete items"
  else
    echo "✗ Editor failed to delete item"
  fi
fi

if [ -n "$ITEM_ID" ]; then
  echo "Admin deleting item:"
  RESPONSE=$(curl -s -X DELETE "$BASE_URL/reporting-effort-items/$ITEM_ID" -H "$ADMIN_HEADER")
  
  if echo "$RESPONSE" | grep -q '"message".*"deleted"'; then
    echo "✓ Admin can delete items"
  else
    echo "✗ Admin failed to delete item"
  fi
fi
echo ""

# Test 8: Bulk operations (admin only)
echo "Test 8: Testing bulk operations permissions"
echo "Admin attempting bulk upload:"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/bulk-upload" \
  -H "Content-Type: application/json" \
  -H "$ADMIN_HEADER" \
  -d '{
    "reporting_effort_id": 1,
    "items": [
      {
        "item_type": "TLF",
        "item_subtype": "Table",
        "item_code": "T_BULK_1"
      },
      {
        "item_type": "TLF",
        "item_subtype": "Figure",
        "item_code": "F_BULK_1"
      }
    ]
  }')

if echo "$RESPONSE" | grep -q '"created_count"'; then
  echo "✓ Admin can perform bulk uploads"
else
  echo "✗ Admin failed bulk upload"
fi

echo "Editor attempting bulk upload (should fail):"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/bulk-upload" \
  -H "Content-Type: application/json" \
  -H "$EDITOR_HEADER" \
  -d '{
    "reporting_effort_id": 1,
    "items": [
      {
        "item_type": "TLF",
        "item_subtype": "Table",
        "item_code": "T_BULK_2"
      }
    ]
  }')

if echo "$RESPONSE" | grep -q '"detail".*"permission"'; then
  echo "✓ Editor correctly denied bulk upload permission"
elif echo "$RESPONSE" | grep -q '"created_count"'; then
  echo "✗ Security issue: Editor was able to bulk upload!"
else
  echo "? Unexpected response for editor bulk upload"
fi

echo "Viewer attempting bulk upload (should fail):"
RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/bulk-upload" \
  -H "Content-Type: application/json" \
  -H "$VIEWER_HEADER" \
  -d '{
    "reporting_effort_id": 1,
    "items": [
      {
        "item_type": "TLF",
        "item_subtype": "Table",
        "item_code": "T_BULK_3"
      }
    ]
  }')

if echo "$RESPONSE" | grep -q '"detail".*"permission"'; then
  echo "✓ Viewer correctly denied bulk upload permission"
elif echo "$RESPONSE" | grep -q '"created_count"'; then
  echo "✗ Security issue: Viewer was able to bulk upload!"
else
  echo "? Unexpected response for viewer bulk upload"
fi
echo ""

echo "========================================"
echo "Role-Based Permission Testing Complete"
echo "========================================"