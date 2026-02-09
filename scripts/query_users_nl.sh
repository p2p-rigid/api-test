#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"your natural language query\""
  echo "Example: $0 \"find user email is john@example.com\""
  exit 1
fi

QUERY="$*"
API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
PROVIDER="${NL_PROVIDER:-openrouter}"
LIMIT="${NL_LIMIT:-20}"

if [[ "$PROVIDER" != "google" && "$PROVIDER" != "openrouter" ]]; then
  echo "Error: NL_PROVIDER must be 'google' or 'openrouter'"
  exit 1
fi

PAYLOAD=$(QUERY="$QUERY" PROVIDER="$PROVIDER" LIMIT="$LIMIT" python3 - <<'PY'
import json
import os

print(
    json.dumps(
        {
            "query": os.environ["QUERY"],
            "provider": os.environ["PROVIDER"],
            "limit": int(os.environ["LIMIT"]),
        }
    )
)
PY
)

curl -sS -X POST "$API_BASE_URL/api/v1/agents/users/query" \
  -H 'Content-Type: application/json' \
  -d "$PAYLOAD"

echo
