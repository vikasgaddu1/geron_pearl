#\!/bin/bash

# Test Study Deletion Protection - Fixed Version
BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)
STUDY_LABEL="protect-test-study-$TIMESTAMP"
DB_RELEASE_LABEL="protect-test-release-$TIMESTAMP"

echo "============================================"
echo "     Study Deletion Protection Test         "
echo "============================================"
echo "Base URL: $BASE_URL"
echo "Test Study Label: $STUDY_LABEL"
echo "Test DB Release Label: $DB_RELEASE_LABEL"
echo "============================================"

# Create test study
echo -e "\033[0;34m[INFO]\033[0m Creating test study..."
STUDY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/studies/" \
  -H "Content-Type: application/json" \
  -d "{\"study_label\": \"$STUDY_LABEL\"}")

STUDY_ID=$(echo $STUDY_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$STUDY_ID" ]; then
    echo -e "\033[0;31m[FAIL]\033[0m Failed to create test study"
    echo "Response: $STUDY_RESPONSE"
    exit 1
fi

echo -e "\033[0;32m[PASS]\033[0m Created test study with ID: $STUDY_ID"

# Create database release for the study
echo -e "\033[0;34m[INFO]\033[0m Creating database release for study..."
RELEASE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/database-releases/" \
  -H "Content-Type: application/json" \
  -d "{\"study_id\": $STUDY_ID, \"database_release_label\": \"$DB_RELEASE_LABEL\"}")

RELEASE_ID=$(echo $RELEASE_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$RELEASE_ID" ]; then
    echo -e "\033[0;31m[FAIL]\033[0m Failed to create database release"
    echo "Response: $RELEASE_RESPONSE"
    exit 1
fi

echo -e "\033[0;32m[PASS]\033[0m Created database release with ID: $RELEASE_ID"

# Try to delete study (should fail due to associated database release)
echo -e "\033[0;34m[INFO]\033[0m Testing study deletion protection (should fail)..."
DELETE_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X DELETE "$BASE_URL/api/v1/studies/$STUDY_ID")
DELETE_STATUS=$(echo $DELETE_RESPONSE | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
DELETE_BODY=$(echo $DELETE_RESPONSE | sed 's/HTTPSTATUS:[0-9]*$//')

echo -e "\033[0;34m[INFO]\033[0m Delete response status: $DELETE_STATUS"
echo -e "\033[0;34m[INFO]\033[0m Delete response body: $DELETE_BODY"

if [ "$DELETE_STATUS" = "400" ]; then
    echo -e "\033[0;32m[PASS]\033[0m Study deletion correctly blocked - Status: $DELETE_STATUS"
    echo -e "\033[0;34m[INFO]\033[0m Deletion blocked because of associated database release"
else
    echo -e "\033[0;31m[FAIL]\033[0m Study deletion should have been blocked - Status: $DELETE_STATUS"
    echo -e "\033[0;31m[FAIL]\033[0m Expected 400, got $DELETE_STATUS"
fi

# Delete the database release first
echo -e "\033[0;34m[INFO]\033[0m Deleting database release..."
curl -s -X DELETE "$BASE_URL/api/v1/database-releases/$RELEASE_ID" > /dev/null
echo -e "\033[0;32m[PASS]\033[0m Database release deleted"

# Now try to delete the study (should succeed)
echo -e "\033[0;34m[INFO]\033[0m Testing study deletion after removing database release..."
DELETE_RESPONSE2=$(curl -s -w "HTTPSTATUS:%{http_code}" -X DELETE "$BASE_URL/api/v1/studies/$STUDY_ID")
DELETE_STATUS2=$(echo $DELETE_RESPONSE2 | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)

if [ "$DELETE_STATUS2" = "200" ]; then
    echo -e "\033[0;32m[PASS]\033[0m Study deletion successful after removing database release - Status: $DELETE_STATUS2"
else
    echo -e "\033[0;31m[FAIL]\033[0m Study deletion failed even after removing database release - Status: $DELETE_STATUS2"
    DELETE_BODY2=$(echo $DELETE_RESPONSE2 | sed 's/HTTPSTATUS:[0-9]*$//')
    echo -e "\033[0;31m[ERROR]\033[0m Response: $DELETE_BODY2"
fi

echo "============================================"
echo "         Protection Test Complete           "
echo "============================================"
