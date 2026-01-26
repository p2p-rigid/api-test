#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run a SQL query against the project's PostgreSQL using psql.

Usage:
  ./psql_query.sh "SELECT now();"
  DB_URL=postgresql://user:pass@host:5432/db ./psql_query.sh "SELECT 1;"

Notes:
  - Reads DB URL from DB_URL or DATABASE_URL env vars, otherwise parses app/config/settings.py.
  - Converts SQLAlchemy async URL (postgresql+asyncpg://...) to psql format (postgresql://...).
  - Stops on SQL errors and disables pager for clean output.
EOF
}

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found. Please install the PostgreSQL client tools." >&2
  exit 127
fi

if [[ ${1-} == "-h" || ${1-} == "--help" || $# -eq 0 ]]; then
  usage
  exit 0
fi

# Combine all args into a single query string to allow spaces/newlines when quoted by caller
QUERY="$*"

# If it's not a psql meta-command (\...), ensure it ends with a semicolon so -c executes it.
if [[ ${QUERY:0:1} != "\\" && ${QUERY} != *";" ]]; then
  QUERY+=";"
fi

# Determine DB URL: prefer env vars, else parse from settings.py
URL="${DB_URL:-${DATABASE_URL:-}}"
if [[ -z "$URL" && -f app/config/settings.py ]]; then
  # Extract the value between quotes on the database_url assignment line
  URL=$(awk -F'"' '/database_url\s*:\s*str\s*=/{print $2; exit}' app/config/settings.py || true)
fi

if [[ -z "$URL" ]]; then
  echo "Could not determine database URL. Set DB_URL or DATABASE_URL, or ensure app/config/settings.py contains database_url." >&2
  exit 1
fi

# Convert SQLAlchemy async URL (postgresql+asyncpg) to psql-compatible
URL="${URL/postgresql+asyncpg:/postgresql:}"
URL="${URL/postgres+asyncpg:/postgres:}"

# Execute the query
exec psql -X -v ON_ERROR_STOP=1 -P pager=off "$URL" -c "$QUERY"

