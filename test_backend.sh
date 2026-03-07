#!/bin/bash

# OSINT Backend Diagnostic Test Suite
# Purpose: Test each endpoint independently to identify failures
# Run: bash test_backend.sh

API_BASE="http://127.0.0.1:5000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== OSINT Backend Diagnostic Tests ===${NC}\n"

# TEST 1: Health Check
echo -e "${YELLOW}TEST 1: Health Check${NC}"
echo "Command: GET /api/health"
echo "Expected: HTTP 200, status: 'online'"
echo ""
curl -s -X GET "$API_BASE/api/health" | jq . 2>/dev/null || curl -s -X GET "$API_BASE/api/health"
echo -e "\n---\n"

# TEST 2: Phone Lookup (Format: +233XXXXXXXXX)
echo -e "${YELLOW}TEST 2: Phone Lookup (+233 format)${NC}"
echo "Command: POST /api/phone/lookup"
echo "Payload: { phone_number: '+233 24 1111 1111', country_code: null, scan_type: 'light' }"
echo "Expected: HTTP 200, target: '+233...', threat_level: >= 0"
echo ""
curl -s -X POST "$API_BASE/api/phone/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+233 24 1111 1111",
    "country_code": null,
    "scan_type": "light"
  }' | jq . 2>/dev/null || curl -s -X POST "$API_BASE/api/phone/lookup" \
  -H "Content-Type: application/json" \
  -d '{ "phone_number": "+233 24 1111 1111", "scan_type": "light" }'
echo -e "\n---\n"

# TEST 3: Phone Lookup (Format: 024XXXXXXXXX - Local Ghana format)
echo -e "${YELLOW}TEST 3: Phone Lookup (024 format - Local)${NC}"
echo "Command: POST /api/phone/lookup"
echo "Payload: { phone_number: '024 1111 1111', country_code: 'GH', scan_type: 'light' }"
echo "Expected: HTTP 200, normalized: '+233...', no 400 error"
echo ""
curl -s -X POST "$API_BASE/api/phone/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "024 1111 1111",
    "country_code": "GH",
    "scan_type": "light"
  }' | jq . 2>/dev/null || curl -s -X POST "$API_BASE/api/phone/lookup" \
  -H "Content-Type: application/json" \
  -d '{ "phone_number": "024 1111 1111", "country_code": "GH", "scan_type": "light" }'
echo -e "\n---\n"

# TEST 4: Phone Lookup (Format: 233XXXXXXXXX - No + prefix)
echo -e "${YELLOW}TEST 4: Phone Lookup (233 format - No + prefix)${NC}"
echo "Command: POST /api/phone/lookup"
echo "Payload: { phone_number: '233 24 1111 1111' }"
echo "Expected: HTTP 200, normalized properly, no 400"
echo ""
curl -s -X POST "$API_BASE/api/phone/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "233 24 1111 1111",
    "scan_type": "light"
  }' | jq . 2>/dev/null || curl -s -X POST "$API_BASE/api/phone/lookup" \
  -H "Content-Type: application/json" \
  -d '{ "phone_number": "233 24 1111 1111", "scan_type": "light" }'
echo -e "\n---\n"

# TEST 5: Phone Lookup - Missing phone number
echo -e "${YELLOW}TEST 5: Phone Lookup - Error: Missing phone number${NC}"
echo "Command: POST /api/phone/lookup"
echo "Payload: {} (empty)"
echo "Expected: HTTP 400, error message"
echo ""
curl -s -X POST "$API_BASE/api/phone/lookup" \
  -H "Content-Type: application/json" \
  -d '{}' | jq . 2>/dev/null || curl -s -X POST "$API_BASE/api/phone/lookup" \
  -H "Content-Type: application/json" \
  -d '{}'
echo -e "\n---\n"

# TEST 6: Create Investigation
echo -e "${YELLOW}TEST 6: Create Investigation${NC}"
echo "Command: POST /api/investigation/create"
echo "Payload: { username: 'testuser', email: 'test@example.com' }"
echo "Expected: HTTP 200, case_id: 'CASE...' (save this for next test)"
echo ""
CASE_RESPONSE=$(curl -s -X POST "$API_BASE/api/investigation/create" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com"
  }')
echo "$CASE_RESPONSE" | jq . 2>/dev/null || echo "$CASE_RESPONSE"

# Extract case_id if successful
CASE_ID=$(echo "$CASE_RESPONSE" | jq -r '.data.case_id // .case_id // empty' 2>/dev/null)
if [ ! -z "$CASE_ID" ]; then
    echo -e "${GREEN}✓ Case ID extracted: $CASE_ID${NC}\n"
else
    echo -e "${RED}✗ Failed to extract case_id${NC}\n"
fi
echo "---"
echo ""

# TEST 7: Start Light Scan (if case was created)
if [ ! -z "$CASE_ID" ]; then
    echo -e "${YELLOW}TEST 7: Start Light Scan${NC}"
    echo "Command: POST /api/investigation/scan/$CASE_ID/light"
    echo "Expected: HTTP 200, threat_level: >= 0 (NOT 500)"
    echo ""
    curl -s -X POST "$API_BASE/api/investigation/scan/$CASE_ID/light" \
      -H "Content-Type: application/json" \
      -d '{}' | jq . 2>/dev/null || curl -s -X POST "$API_BASE/api/investigation/scan/$CASE_ID/light"
    echo -e "\n---\n"
else
    echo -e "${RED}TEST 7: SKIPPED (no case_id)${NC}\n"
fi

# TEST 8: Get Investigation Status
if [ ! -z "$CASE_ID" ]; then
    echo -e "${YELLOW}TEST 8: Get Investigation Status${NC}"
    echo "Command: GET /api/investigation/status/$CASE_ID"
    echo "Expected: HTTP 200, status: 'completed' or 'running'"
    echo ""
    curl -s -X GET "$API_BASE/api/investigation/status/$CASE_ID" | jq . 2>/dev/null || curl -s -X GET "$API_BASE/api/investigation/status/$CASE_ID"
    echo -e "\n---\n"
else
    echo -e "${RED}TEST 8: SKIPPED (no case_id)${NC}\n"
fi

# TEST 9: Get Investigation Result
if [ ! -z "$CASE_ID" ]; then
    echo -e "${YELLOW}TEST 9: Get Investigation Result${NC}"
    echo "Command: GET /api/investigation/result/$CASE_ID"
    echo "Expected: HTTP 200, response with threat_level field"
    echo ""
    curl -s -X GET "$API_BASE/api/investigation/result/$CASE_ID" | jq . 2>/dev/null || curl -s -X GET "$API_BASE/api/investigation/result/$CASE_ID"
    echo -e "\n---\n"
else
    echo -e "${RED}TEST 9: SKIPPED (no case_id)${NC}\n"
fi

echo -e "${BLUE}=== Diagnostic Tests Complete ===${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "If you see HTTP 400: Check request payload validation"
echo "If you see HTTP 500: Check Exception handler in routes"
echo "If threat_level is 10 with no data: Check analyzer.py threat scoring"
echo "If no data returned: Check service functions (phone_intel.py, scraper.py)"
echo ""
echo -e "${YELLOW}Check logs with:${NC}"
echo "  grep -E '\[PHONE_LOOKUP\]|\[SCAN\]|\[THREAT_SCORING\]' flask.log"
