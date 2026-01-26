#!/bin/bash

# End-to-End Test Script for User Services
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

# Function to run a test
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_status="$3"

    print_info "Running: $test_name"

    # Execute the command and capture status
    local http_status
    http_status=$(eval "$command")
    local status=$?

    if [ "$status" -eq 0 ] && [ "$http_status" = "$expected_status" ]; then
        print_status "$test_name - Expected status $expected_status, got $http_status"
    else
        print_error "$test_name - Expected status $expected_status, got $http_status or error"
        return 1
    fi
}

# Start the application in the background
print_info "Starting the application..."
cd /home/robert/work/api-test-worktree-1
source .venv/bin/activate
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
APP_PID=$!

# Wait for the app to start
sleep 5

# Test if the app is running
if ! curl -s "$BASE_URL/health" > /dev/null; then
    print_error "Application failed to start"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

print_status "Application started successfully"

# Test variables with unique values for each run
TIMESTAMP=$(date +%s)
TEST_USER_EMAIL="testuser_${TIMESTAMP}@example.com"
TEST_USER_USERNAME="testuser_${TIMESTAMP}"
TEST_USER_PASSWORD="TestPass123!"
TEST_USER_FIRST_NAME="Test"
TEST_USER_LAST_NAME="User"

# Test 1: Health check
run_test "Health Check" \
    "curl -s -o /dev/null -w '%{http_code}' $BASE_URL/health" \
    "200"

# Test 2: Root endpoint
run_test "Root Endpoint" \
    "curl -s -o /dev/null -w '%{http_code}' $BASE_URL/" \
    "200"

# Test 3: Create a user (Happy Path)
print_info "Creating a user..."
CREATE_USER_RESPONSE=$(curl -s -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\", \"username\":\"$TEST_USER_USERNAME\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

CREATE_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\", \"username\":\"$TEST_USER_USERNAME\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

if [ "$CREATE_STATUS" = "201" ]; then
    USER_ID=$(echo "$CREATE_USER_RESPONSE" | grep -o '"id":[0-9]*' | cut -d: -f2 | head -1)
    print_status "User created successfully with ID: $USER_ID"
else
    print_error "Failed to create user. Status: $CREATE_STATUS"
    echo "$CREATE_USER_RESPONSE"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

# Test 4: Get the created user
run_test "Get User by ID" \
    "curl -s -o /dev/null -w '%{http_code}' $API_BASE/users/$USER_ID" \
    "200"

# Test 5: Get all users
run_test "Get All Users" \
    "curl -s -o /dev/null -w '%{http_code}' $API_BASE/users/" \
    "200"

# Test 6: Update user
UPDATE_USER_RESPONSE=$(curl -s -X PATCH "$API_BASE/users/$USER_ID" \
    -H "Content-Type: application/json" \
    -d "{\"first_name\":\"Updated\", \"last_name\":\"Name\"}")

UPDATE_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X PATCH "$API_BASE/users/$USER_ID" \
    -H "Content-Type: application/json" \
    -d "{\"first_name\":\"Updated\", \"last_name\":\"Name\"}")

if [ "$UPDATE_STATUS" = "200" ]; then
    print_status "User updated successfully"
else
    print_error "Failed to update user. Status: $UPDATE_STATUS"
    echo "$UPDATE_USER_RESPONSE"
fi

# Test 7: Try to create user with duplicate email (Validation Error)
DUPLICATE_EMAIL_RESPONSE=$(curl -s -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\", \"username\":\"differentuser\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

DUPLICATE_EMAIL_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\", \"username\":\"differentuser\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

if [ "$DUPLICATE_EMAIL_STATUS" = "409" ]; then
    print_status "Duplicate email validation works correctly"
else
    print_error "Duplicate email validation failed. Status: $DUPLICATE_EMAIL_STATUS"
    echo "$DUPLICATE_EMAIL_RESPONSE"
fi

# Test 8: Try to create user with duplicate username (Validation Error)
DUPLICATE_USERNAME_RESPONSE=$(curl -s -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"different@example.com\", \"username\":\"$TEST_USER_USERNAME\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

DUPLICATE_USERNAME_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"different@example.com\", \"username\":\"$TEST_USER_USERNAME\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

if [ "$DUPLICATE_USERNAME_STATUS" = "409" ]; then
    print_status "Duplicate username validation works correctly"
else
    print_error "Duplicate username validation failed. Status: $DUPLICATE_USERNAME_STATUS"
    echo "$DUPLICATE_USERNAME_RESPONSE"
fi

# Test 9: Try to create user with invalid email (Validation Error)
INVALID_EMAIL_RESPONSE=$(curl -s -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"invalid-email\", \"username\":\"invaliduser\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

INVALID_EMAIL_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"invalid-email\", \"username\":\"invaliduser\", \"password\":\"$TEST_USER_PASSWORD\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

if [ "$INVALID_EMAIL_STATUS" = "422" ]; then
    print_status "Invalid email validation works correctly"
else
    print_error "Invalid email validation failed. Status: $INVALID_EMAIL_STATUS"
    echo "$INVALID_EMAIL_RESPONSE"
fi

# Test 10: Try to create user with weak password (Validation Error)
WEAK_PASSWORD_RESPONSE=$(curl -s -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"weakpass@example.com\", \"username\":\"weakpassuser\", \"password\":\"weak\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

WEAK_PASSWORD_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API_BASE/users/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"weakpass@example.com\", \"username\":\"weakpassuser\", \"password\":\"weak\", \"first_name\":\"$TEST_USER_FIRST_NAME\", \"last_name\":\"$TEST_USER_LAST_NAME\"}")

if [ "$WEAK_PASSWORD_STATUS" = "422" ]; then
    print_status "Weak password validation works correctly"
else
    print_error "Weak password validation failed. Status: $WEAK_PASSWORD_STATUS"
    echo "$WEAK_PASSWORD_RESPONSE"
fi

# Test 11: Soft delete user
DELETE_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$API_BASE/users/$USER_ID")
if [ "$DELETE_STATUS" = "204" ]; then
    print_status "User soft deleted successfully"
else
    print_error "Failed to delete user. Status: $DELETE_STATUS"
fi

# Test 12: Try to get non-existent user (after deletion)
GET_DELETED_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$API_BASE/users/$USER_ID")
if [ "$GET_DELETED_STATUS" = "200" ]; then
    print_info "User still accessible after soft delete (as expected for soft delete)"
else
    print_error "Unexpected status for deleted user: $GET_DELETED_STATUS"
fi

# Test 13: Try to get user with invalid ID
GET_INVALID_STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$API_BASE/users/999999")
if [ "$GET_INVALID_STATUS" = "404" ]; then
    print_status "Invalid user ID validation works correctly"
else
    print_error "Invalid user ID validation failed. Status: $GET_INVALID_STATUS"
fi

print_info "Stopping the application..."
kill $APP_PID 2>/dev/null || true

print_info "End-to-End Test Script Completed"
print_status "All tests have been executed. Check the output above for any failures."