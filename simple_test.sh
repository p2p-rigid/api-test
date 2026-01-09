#!/bin/bash

# Simple End-to-End Test Script for User Services
# This script tests all user services including happy path and validation errors

set -e  # Exit on any error

# Configuration
BASE_URL="http://localhost:8000"
API_BASE="${BASE_URL}/api/v1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Start the application in the background
print_info "Starting the application..."
cd /home/robert/work/api-test-worktree-1
source .venv/bin/activate
pkill -f "uvicorn" || true  # Kill any existing uvicorn processes
sleep 2
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > app.log 2>&1 &
APP_PID=$!

# Wait for the app to start
sleep 10

# Test if the app is running
if ! curl -s "$BASE_URL/health" > /dev/null; then
    print_error "Application failed to start"
    pkill -f uvicorn 2>/dev/null || true
    exit 1
fi

print_status "Application started successfully"

# Generate unique values for this test run
TIMESTAMP=$(date +%s)
TEST_USER_EMAIL="testuser_${TIMESTAMP}@example.com"
TEST_USER_USERNAME="testuser_${TIMESTAMP}"
TEST_USER_PASSWORD="TestPass123!"
TEST_USER_FIRST_NAME="Test"
TEST_USER_LAST_NAME="User"

print_info "Testing Health Check..."
HEALTH_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/health")
if [ "$HEALTH_STATUS" = "200" ]; then
    print_status "Health Check - Status: $HEALTH_STATUS"
else
    print_error "Health Check failed - Status: $HEALTH_STATUS"
    pkill -f uvicorn 2>/dev/null || true
    exit 1
fi

print_info "Testing Root Endpoint..."
ROOT_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/")
if [ "$ROOT_STATUS" = "200" ]; then
    print_status "Root Endpoint - Status: $ROOT_STATUS"
else
    print_error "Root Endpoint failed - Status: $ROOT_STATUS"
    pkill -f uvicorn 2>/dev/null || true
    exit 1
fi

print_info "Creating a user..."
CREATE_RESPONSE=$(curl -s -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\", \"username\":\"$TEST_USER_USERNAME\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

CREATE_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\", \"username\":\"$TEST_USER_USERNAME\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

if [ "$CREATE_STATUS" = "201" ]; then
    USER_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'NOT_FOUND'))")
    print_status "User created successfully with ID: $USER_ID"
else
    print_error "Failed to create user. Status: $CREATE_STATUS"
    echo "$CREATE_RESPONSE"
    pkill -f uvicorn 2>/dev/null || true
    exit 1
fi

print_info "Getting the created user..."
GET_USER_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$API_BASE/users/$USER_ID")
if [ "$GET_USER_STATUS" = "200" ]; then
    print_status "Get user by ID - Status: $GET_USER_STATUS"
else
    print_error "Get user by ID failed - Status: $GET_USER_STATUS"
fi

print_info "Getting all users..."
GET_ALL_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$API_BASE/users/")
if [ "$GET_ALL_STATUS" = "200" ]; then
    print_status "Get all users - Status: $GET_ALL_STATUS"
else
    print_error "Get all users failed - Status: $GET_ALL_STATUS"
fi

print_info "Updating user..."
UPDATE_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X PATCH "$API_BASE/users/$USER_ID" \
    -H "Content-Type: application/json" \
    -d "{\"first_name\":\"Updated\", \"last_name\":\"Name\"}")
if [ "$UPDATE_STATUS" = "200" ]; then
    print_status "Update user - Status: $UPDATE_STATUS"
else
    print_error "Update user failed - Status: $UPDATE_STATUS"
fi

print_info "Testing duplicate email validation..."
DUPLICATE_EMAIL_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\", \"username\":\"differentuser_${TIMESTAMP}\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")
if [ "$DUPLICATE_EMAIL_STATUS" = "409" ]; then
    print_status "Duplicate email validation - Status: $DUPLICATE_EMAIL_STATUS"
else
    print_error "Duplicate email validation failed - Status: $DUPLICATE_EMAIL_STATUS"
fi

print_info "Testing duplicate username validation..."
DUPLICATE_USERNAME_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"different_${TIMESTAMP}@example.com\", \"username\":\"$TEST_USER_USERNAME\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")
if [ "$DUPLICATE_USERNAME_STATUS" = "409" ]; then
    print_status "Duplicate username validation - Status: $DUPLICATE_USERNAME_STATUS"
else
    print_error "Duplicate username validation failed - Status: $DUPLICATE_USERNAME_STATUS"
fi

print_info "Testing invalid email validation..."
INVALID_EMAIL_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"invalid-email\", \"username\":\"invaliduser_${TIMESTAMP}\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")
if [ "$INVALID_EMAIL_STATUS" = "422" ]; then
    print_status "Invalid email validation - Status: $INVALID_EMAIL_STATUS"
else
    print_error "Invalid email validation failed - Status: $INVALID_EMAIL_STATUS"
fi

print_info "Testing weak password validation..."
WEAK_PASSWORD_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"weakpass_${TIMESTAMP}@example.com\", \"username\":\"weakpassuser_${TIMESTAMP}\", \"password\":\"weak\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")
if [ "$WEAK_PASSWORD_STATUS" = "422" ]; then
    print_status "Weak password validation - Status: $WEAK_PASSWORD_STATUS"
else
    print_error "Weak password validation failed - Status: $WEAK_PASSWORD_STATUS"
fi

print_info "Soft deleting user..."
DELETE_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$API_BASE/users/$USER_ID")
if [ "$DELETE_STATUS" = "204" ]; then
    print_status "Soft delete user - Status: $DELETE_STATUS"
else
    print_error "Soft delete user failed - Status: $DELETE_STATUS"
fi

print_info "Testing invalid user ID..."
INVALID_ID_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$API_BASE/users/999999")
if [ "$INVALID_ID_STATUS" = "404" ]; then
    print_status "Invalid user ID validation - Status: $INVALID_ID_STATUS"
else
    print_error "Invalid user ID validation failed - Status: $INVALID_ID_STATUS"
fi

print_info "Stopping the application..."
pkill -f uvicorn 2>/dev/null || true

print_info "Simple End-to-End Test Script Completed"
print_status "All tests have been executed. Check the output above for any failures."