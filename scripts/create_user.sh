#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
EMAIL="${EMAIL:-alice.$(date +%s)@example.com}"
USERNAME="${USERNAME:-alice$RANDOM}"

curl -fsS -X POST "$BASE_URL/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "email": "$EMAIL",
  "username": "$USERNAME",
  "first_name": "Alice",
  "last_name": "Smith",
  "password": "SecurePass1!"
}
JSON
