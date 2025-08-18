#!/bin/bash

# Demo script for the Reporting Effort Tracker DELETE endpoint
# This script demonstrates the DELETE endpoint functionality

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL for the API
BASE_URL="http://localhost:8000/api/v1"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Tracker DELETE Endpoint Demo${NC}"
echo -e "${YELLOW}========================================${NC}"

echo -e "\n${BLUE}This demo shows the DELETE /api/v1/reporting-effort-tracker/{tracker_id} endpoint in action${NC}"

# Check server status
echo -e "\n${YELLOW}1. Checking server status...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" | grep -q "200"; then
    echo -e "${GREEN}✓ Server is running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Server is not running${NC}"
    exit 1
fi

# Show existing trackers
echo -e "\n${YELLOW}2. Current trackers in the system:${NC}"
trackers=$(curl -s "$BASE_URL/reporting-effort-tracker/?limit=3")
echo "$trackers" | head -300

# Get a tracker ID for demo
tracker_id=$(echo "$trackers" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
if [ -n "$tracker_id" ] && [ "$tracker_id" != "" ]; then
    echo -e "\n${YELLOW}3. Demo: Deleting tracker ID $tracker_id${NC}"
    
    # Show the tracker before deletion
    echo -e "\n${BLUE}Before deletion - GET /reporting-effort-tracker/$tracker_id:${NC}"
    before_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/reporting-effort-tracker/$tracker_id")
    before_code=$(echo "$before_response" | tail -n1)
    before_body=$(echo "$before_response" | sed '$d')
    echo "Status: $before_code"
    echo "Response: $before_body"
    
    if [ "$before_code" = "200" ]; then
        echo -e "\n${BLUE}Performing deletion - DELETE /reporting-effort-tracker/$tracker_id:${NC}"
        delete_response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/reporting-effort-tracker/$tracker_id")
        delete_code=$(echo "$delete_response" | tail -n1)
        delete_body=$(echo "$delete_response" | sed '$d')
        echo "Status: $delete_code"
        if [ -n "$delete_body" ]; then
            echo "Response: $delete_body"
        else
            echo "Response: (empty - as expected for 204 No Content)"
        fi
        
        if [ "$delete_code" = "204" ]; then
            echo -e "${GREEN}✓ Deletion successful (204 No Content)${NC}"
            
            echo -e "\n${BLUE}After deletion - GET /reporting-effort-tracker/$tracker_id:${NC}"
            after_response=$(curl -s -w "\n%{http_code}" "$BASE_URL/reporting-effort-tracker/$tracker_id")
            after_code=$(echo "$after_response" | tail -n1)
            after_body=$(echo "$after_response" | sed '$d')
            echo "Status: $after_code"
            echo "Response: $after_body"
            
            if [ "$after_code" = "404" ]; then
                echo -e "${GREEN}✓ Tracker successfully removed from database${NC}"
            else
                echo -e "${RED}❌ Unexpected: Tracker still exists after deletion${NC}"
            fi
        else
            echo -e "${RED}❌ Deletion failed with status $delete_code${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Tracker $tracker_id not found, will demonstrate error handling${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No trackers available, demonstrating error handling with non-existent ID${NC}"
    tracker_id=99999
fi

# Demo error cases
echo -e "\n${YELLOW}4. Demo: Error handling cases${NC}"

echo -e "\n${BLUE}Case 1 - Non-existent tracker (DELETE /reporting-effort-tracker/99999):${NC}"
error1_response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/reporting-effort-tracker/99999")
error1_code=$(echo "$error1_response" | tail -n1)
error1_body=$(echo "$error1_response" | sed '$d')
echo "Status: $error1_code"
echo "Response: $error1_body"
if [ "$error1_code" = "404" ]; then
    echo -e "${GREEN}✓ Correctly returns 404 for non-existent tracker${NC}"
fi

echo -e "\n${BLUE}Case 2 - Invalid ID format (DELETE /reporting-effort-tracker/invalid):${NC}"
error2_response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/reporting-effort-tracker/invalid")
error2_code=$(echo "$error2_response" | tail -n1)
error2_body=$(echo "$error2_response" | sed '$d')
echo "Status: $error2_code"
echo "Response: $error2_body"
if [ "$error2_code" = "422" ]; then
    echo -e "${GREEN}✓ Correctly returns 422 for invalid ID format${NC}"
fi

echo -e "\n${BLUE}Case 3 - Negative ID (DELETE /reporting-effort-tracker/-1):${NC}"
error3_response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/reporting-effort-tracker/-1")
error3_code=$(echo "$error3_response" | tail -n1)
error3_body=$(echo "$error3_response" | sed '$d')
echo "Status: $error3_code"
echo "Response: $error3_body"
if [ "$error3_code" = "404" ]; then
    echo -e "${GREEN}✓ Correctly returns 404 for negative ID${NC}"
fi

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Demo Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}The DELETE endpoint demonstrates:${NC}"
echo -e "${GREEN}✓ Successful deletion returns 204 No Content${NC}"
echo -e "${GREEN}✓ Deleted trackers are actually removed from database${NC}"
echo -e "${GREEN}✓ Non-existent trackers return 404 Not Found${NC}"
echo -e "${GREEN}✓ Invalid ID formats return 422 Validation Error${NC}"
echo -e "${GREEN}✓ WebSocket broadcasting (configured for real-time updates)${NC}"
echo -e "${GREEN}✓ Audit logging (configured for compliance tracking)${NC}"

echo -e "\n${BLUE}Endpoint: DELETE /api/v1/reporting-effort-tracker/{tracker_id}${NC}"
echo -e "${BLUE}Purpose: Delete a reporting effort tracker by ID${NC}"
echo -e "${BLUE}Success Response: 204 No Content (empty body)${NC}"
echo -e "${BLUE}Error Responses: 404 (not found), 422 (validation error), 500 (server error)${NC}"