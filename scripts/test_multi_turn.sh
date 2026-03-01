#!/bin/bash

# Multi-turn conversation test script

BASE_URL="http://localhost:8000/api/v1/agents/users/query"
USER_ID="user123"
PROVIDER="openrouter"

echo "========================================="
echo "Multi-turn Conversation Test"
echo "========================================="

echo ""
echo "=== Request 1: List all users ==="
RESPONSE1=$(curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d "{\"query\": \"list all users\", \"provider\": \"$PROVIDER\"}")

echo "$RESPONSE1" | python -m json.tool

SESSION_ID=$(echo "$RESPONSE1" | python -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")

if [ -z "$SESSION_ID" ]; then
    echo "ERROR: No session_id returned"
    exit 1
fi

echo ""
echo "=== Session ID: $SESSION_ID ==="
echo ""

echo "=== Request 2: Show only active users (continuing session) ==="
RESPONSE2=$(curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d "{\"query\": \"show only active users\", \"session_id\": \"$SESSION_ID\", \"provider\": \"$PROVIDER\"}")

echo "$RESPONSE2" | python -m json.tool

echo ""
echo "=== Request 3: Find user by email (continuing session) ==="
RESPONSE3=$(curl -s -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d "{\"query\": \"find user with email test@example.com\", \"session_id\": \"$SESSION_ID\", \"provider\": \"$PROVIDER\"}")

echo "$RESPONSE3" | python -m json.tool

echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="