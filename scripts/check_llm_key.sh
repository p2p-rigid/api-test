#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

usage() {
  echo "Usage: $0 <API_KEY> [provider] [model]"
  echo "Provider: google (default) or openrouter"
  echo "Examples:"
  echo "  $0 AIza..."
  echo "  $0 sk-or-v1-... openrouter openai/gpt-4o-mini"
}

if [[ "${1:-}" == "" ]]; then
  usage
  exit 1
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Error: Python not found at $VENV_PYTHON"
  echo "Create venv first: python -m venv .venv && .venv/bin/pip install -e .[dev]"
  exit 1
fi

API_KEY="$1"
PROVIDER="${2:-google}"
MODEL="${3:-}"

if [[ "$PROVIDER" != "google" && "$PROVIDER" != "openrouter" ]]; then
  echo "Error: provider must be 'google' or 'openrouter'"
  exit 1
fi

if [[ -z "$MODEL" ]]; then
  if [[ "$PROVIDER" == "google" ]]; then
    MODEL="gemini-2.0-flash"
  else
    MODEL="openai/gpt-4o-mini"
  fi
fi

export API_KEY PROVIDER MODEL

"$VENV_PYTHON" - <<'PY'
import os
import sys

import requests
from google.genai import Client

api_key = os.environ["API_KEY"]
provider = os.environ["PROVIDER"]
model = os.environ["MODEL"]

try:
    if provider == "google":
        os.environ["GOOGLE_API_KEY"] = api_key
        client = Client()
        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: OK",
        )
        text = (response.text or "").strip()
        if text:
            print(f"SUCCESS: provider=google model={model} response={text}")
        else:
            print(f"FAILED: provider=google model={model} returned empty response")
            sys.exit(2)
    else:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply exactly: OK"}],
                "temperature": 0,
            },
            timeout=20,
        )
        if response.status_code >= 400:
            print(
                f"FAILED: provider=openrouter model={model} "
                f"status={response.status_code} body={response.text[:180]}"
            )
            sys.exit(3)

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if content:
            print(f"SUCCESS: provider=openrouter model={model} response={content[:120]}")
        else:
            print(f"FAILED: provider=openrouter model={model} empty content")
            sys.exit(4)
except Exception as exc:
    print(f"FAILED: provider={provider} model={model} error={type(exc).__name__}: {exc}")
    sys.exit(5)
PY
