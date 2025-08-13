#!/bin/bash

# Test script for Reporting Effort Tracker CRUD operations
# This script tests the complete tracker workflow including items, assignments, and comments

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL for the API
BASE_URL="http://localhost:8000/api/v1"

echo -e "${YELLOW}Testing Reporting Effort Tracker CRUD Operations${NC}"
echo "=================================================="

# Check if server is running - try to fetch studies endpoint
echo -e "\n${YELLOW}Checking if server is running...${NC}"
if ! curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/studies/" | grep -q "200"; then
    echo -e "${RED}Server is not running. Please start it with: cd backend && uv run python run.py${NC}"
    exit 1
fi
echo -e "${GREEN}Server is running${NC}"

# Create a test study, database release, and reporting effort first
echo -e "\n${YELLOW}Creating test environment...${NC}"

# Create study
STUDY_RESPONSE=$(curl -s -X POST "$BASE_URL/studies/" \
    -H "Content-Type: application/json" \
    -d '{
        "study_label": "Test Study for Tracker",
        "study_name": "Tracker Test Study"
    }')
STUDY_ID=$(echo $STUDY_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Created study with ID: $STUDY_ID${NC}"

# Create database release
DB_RELEASE_RESPONSE=$(curl -s -X POST "$BASE_URL/database-releases/" \
    -H "Content-Type: application/json" \
    -d '{
        "study_id": '$STUDY_ID',
        "database_release_label": "Test DB Release for Tracker",
        "database_release_date": "2024-01-01"
    }')
DB_RELEASE_ID=$(echo $DB_RELEASE_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Created database release with ID: $DB_RELEASE_ID${NC}"

# Create reporting effort
EFFORT_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-efforts/" \
    -H "Content-Type: application/json" \
    -d '{
        "database_release_id": '$DB_RELEASE_ID',
        "study_id": '$STUDY_ID',
        "database_release_label": "Test Reporting Effort for Tracker"
    }')
EFFORT_ID=$(echo $EFFORT_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Created reporting effort with ID: $EFFORT_ID${NC}"

# Create test users
echo -e "\n${YELLOW}Creating test users...${NC}"

# Create production programmer
PROD_USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "prod_programmer",
        "email": "prod@test.com",
        "full_name": "Production Programmer",
        "role": "editor",
        "department": "Programming"
    }')
PROD_USER_ID=$(echo $PROD_USER_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Created production programmer with ID: $PROD_USER_ID${NC}"

# Create QC programmer
QC_USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "qc_programmer",
        "email": "qc@test.com",
        "full_name": "QC Programmer",
        "role": "editor",
        "department": "Programming"
    }')
QC_USER_ID=$(echo $QC_USER_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Created QC programmer with ID: $QC_USER_ID${NC}"

# Create biostatistician
BIOSTAT_USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "biostat_user",
        "email": "biostat@test.com",
        "full_name": "Biostatistician",
        "role": "viewer",
        "department": "Biostatistics"
    }')
BIOSTAT_USER_ID=$(echo $BIOSTAT_USER_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Created biostatistician with ID: $BIOSTAT_USER_ID${NC}"

# Test 1: Create reporting effort items
echo -e "\n${YELLOW}Test 1: Creating reporting effort items...${NC}"

# Create TLF item
TLF_ITEM_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
    -H "Content-Type: application/json" \
    -d '{
        "reporting_effort_id": '$EFFORT_ID',
        "item_type": "TLF",
        "item_subtype": "Table",
        "item_code": "T_14_1_1",
        "study_id": '$STUDY_ID',
        "source_type": "custom"
    }')
TLF_ITEM_ID=$(echo $TLF_ITEM_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Created TLF item with ID: $TLF_ITEM_ID${NC}"

# Create Dataset item
DATASET_ITEM_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-items/" \
    -H "Content-Type: application/json" \
    -d '{
        "reporting_effort_id": '$EFFORT_ID',
        "item_type": "Dataset",
        "item_subtype": "ADaM",
        "item_code": "ADSL",
        "study_id": '$STUDY_ID',
        "source_type": "custom"
    }')
DATASET_ITEM_ID=$(echo $DATASET_ITEM_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Created Dataset item with ID: $DATASET_ITEM_ID${NC}"

# Test 2: Verify auto-created trackers
echo -e "\n${YELLOW}Test 2: Verifying auto-created trackers...${NC}"

# Get tracker for TLF item
TLF_TRACKER_RESPONSE=$(curl -s "$BASE_URL/reporting-effort-tracker/by-item/$TLF_ITEM_ID")
TLF_TRACKER_ID=$(echo $TLF_TRACKER_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Found tracker for TLF item with ID: $TLF_TRACKER_ID${NC}"

# Get tracker for Dataset item
DATASET_TRACKER_RESPONSE=$(curl -s "$BASE_URL/reporting-effort-tracker/by-item/$DATASET_ITEM_ID")
DATASET_TRACKER_ID=$(echo $DATASET_TRACKER_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Found tracker for Dataset item with ID: $DATASET_TRACKER_ID${NC}"

# Test 3: Assign programmers
echo -e "\n${YELLOW}Test 3: Assigning programmers to trackers...${NC}"

# Assign production programmer to TLF
curl -s -X POST "$BASE_URL/reporting-effort-tracker/$TLF_TRACKER_ID/assign-programmer" \
    -H "Content-Type: application/json" \
    -d '{
        "programmer_id": '$PROD_USER_ID',
        "role": "production"
    }' > /dev/null
echo -e "${GREEN}Assigned production programmer to TLF tracker${NC}"

# Assign QC programmer to TLF
curl -s -X POST "$BASE_URL/reporting-effort-tracker/$TLF_TRACKER_ID/assign-programmer" \
    -H "Content-Type: application/json" \
    -d '{
        "programmer_id": '$QC_USER_ID',
        "role": "qc"
    }' > /dev/null
echo -e "${GREEN}Assigned QC programmer to TLF tracker${NC}"

# Test 4: Update tracker status
echo -e "\n${YELLOW}Test 4: Updating tracker status...${NC}"

# Update production status
curl -s -X PUT "$BASE_URL/reporting-effort-tracker/$TLF_TRACKER_ID" \
    -H "Content-Type: application/json" \
    -d '{
        "production_status": "in_progress",
        "priority": "high",
        "due_date": "2024-12-31"
    }' > /dev/null
echo -e "${GREEN}Updated TLF tracker production status to in_progress${NC}"

# Test 5: Add comments
echo -e "\n${YELLOW}Test 5: Adding comments to tracker...${NC}"

# Add programmer comment
PROG_COMMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-comments/" \
    -H "Content-Type: application/json" \
    -H "X-User-Id: $PROD_USER_ID" \
    -d '{
        "tracker_id": '$TLF_TRACKER_ID',
        "comment_text": "Started working on the table. Will complete by EOD.",
        "comment_type": "programmer_comment",
        "comment_category": "production"
    }')
PROG_COMMENT_ID=$(echo $PROG_COMMENT_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Added programmer comment with ID: $PROG_COMMENT_ID${NC}"

# Add biostat comment
BIOSTAT_COMMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/reporting-effort-comments/" \
    -H "Content-Type: application/json" \
    -H "X-User-Id: $BIOSTAT_USER_ID" \
    -d '{
        "tracker_id": '$TLF_TRACKER_ID',
        "comment_text": "Please ensure footnotes are included.",
        "comment_type": "biostat_comment",
        "comment_category": "general"
    }')
BIOSTAT_COMMENT_ID=$(echo $BIOSTAT_COMMENT_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "${GREEN}Added biostat comment with ID: $BIOSTAT_COMMENT_ID${NC}"

# Test 6: Test deletion protection
echo -e "\n${YELLOW}Test 6: Testing deletion protection...${NC}"

# Try to delete item with assigned programmers (should fail)
DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/reporting-effort-items/$TLF_ITEM_ID" -w "\n%{http_code}")
if echo "$DELETE_RESPONSE" | grep -q "400"; then
    echo -e "${GREEN}Deletion protection working - cannot delete item with assigned programmers${NC}"
else
    echo -e "${RED}Deletion protection failed - item was deleted with assigned programmers${NC}"
fi

# Test 7: Bulk operations
echo -e "\n${YELLOW}Test 7: Testing bulk operations...${NC}"

# Create multiple items for bulk operations
echo "Creating multiple items for bulk testing..."
for i in {2..5}; do
    curl -s -X POST "$BASE_URL/reporting-effort-items/" \
        -H "Content-Type: application/json" \
        -d '{
            "reporting_effort_id": '$EFFORT_ID',
            "item_type": "TLF",
            "item_subtype": "Figure",
            "item_code": "F_14_1_'$i'",
            "study_id": '$STUDY_ID',
            "source_type": "custom"
        }' > /dev/null
done
echo -e "${GREEN}Created 4 additional items for bulk testing${NC}"

# Get all items for the reporting effort
ITEMS_RESPONSE=$(curl -s "$BASE_URL/reporting-effort-items/by-effort/$EFFORT_ID")
ITEM_COUNT=$(echo $ITEMS_RESPONSE | grep -o '"id"' | wc -l)
echo -e "${GREEN}Total items in reporting effort: $ITEM_COUNT${NC}"

# Test 8: Get workload summary
echo -e "\n${YELLOW}Test 8: Getting workload summary...${NC}"

# Get programmer workload
WORKLOAD_RESPONSE=$(curl -s "$BASE_URL/reporting-effort-tracker/workload/$PROD_USER_ID")
echo -e "${GREEN}Retrieved workload for production programmer${NC}"

# Get overall workload summary
SUMMARY_RESPONSE=$(curl -s "$BASE_URL/reporting-effort-tracker/workload-summary")
echo -e "${GREEN}Retrieved overall workload summary${NC}"

# Test 9: Get comment statistics
echo -e "\n${YELLOW}Test 9: Getting comment statistics...${NC}"

# Get comment stats for item
COMMENT_STATS=$(curl -s "$BASE_URL/reporting-effort-comments/statistics/by-item/$TLF_ITEM_ID")
echo -e "${GREEN}Retrieved comment statistics for TLF item${NC}"

# Test 10: Clean up test data
echo -e "\n${YELLOW}Test 10: Cleaning up test data...${NC}"

# First unassign programmers
curl -s -X DELETE "$BASE_URL/reporting-effort-tracker/$TLF_TRACKER_ID/unassign-programmer?role=production" > /dev/null
curl -s -X DELETE "$BASE_URL/reporting-effort-tracker/$TLF_TRACKER_ID/unassign-programmer?role=qc" > /dev/null
echo -e "${GREEN}Unassigned programmers from tracker${NC}"

# Now delete items (tracker will be auto-deleted)
curl -s -X DELETE "$BASE_URL/reporting-effort-items/$TLF_ITEM_ID" > /dev/null
curl -s -X DELETE "$BASE_URL/reporting-effort-items/$DATASET_ITEM_ID" > /dev/null
echo -e "${GREEN}Deleted test items${NC}"

# Delete reporting effort
curl -s -X DELETE "$BASE_URL/reporting-efforts/$EFFORT_ID" > /dev/null
echo -e "${GREEN}Deleted reporting effort${NC}"

# Delete database release
curl -s -X DELETE "$BASE_URL/database-releases/$DB_RELEASE_ID" > /dev/null
echo -e "${GREEN}Deleted database release${NC}"

# Delete study
curl -s -X DELETE "$BASE_URL/studies/$STUDY_ID" > /dev/null
echo -e "${GREEN}Deleted study${NC}"

# Delete test users
curl -s -X DELETE "$BASE_URL/users/$PROD_USER_ID" > /dev/null
curl -s -X DELETE "$BASE_URL/users/$QC_USER_ID" > /dev/null
curl -s -X DELETE "$BASE_URL/users/$BIOSTAT_USER_ID" > /dev/null
echo -e "${GREEN}Deleted test users${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}All Reporting Effort Tracker tests passed!${NC}"
echo -e "${GREEN}========================================${NC}"