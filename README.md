# API Test - FastAPI with Google ADK Agents

A FastAPI application demonstrating Google Agent Development Kit (ADK) integration for natural language queries on user data, with a Next.js chat frontend and Playwright e2e tests.

## Quick Start

### Backend

```bash
# 1. Install dependencies (use pyproject.toml as source of truth)
pip install -e ".[dev]"

# Note: requirements.txt also exists for compatibility but pyproject.toml
# is the authoritative dependency source and includes [dev] extras.

# 2. Configure environment
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY or GOOGLE_API_KEY

# 3. Start PostgreSQL and create database
psql -U postgres -c "CREATE DATABASE api_test;"

# 4. Run database migrations
alembic upgrade head

# 5. Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Open in browser
# API:       http://localhost:8000
# Swagger:   http://localhost:8000/docs
```

### Frontend (Next.js Chat UI)

```bash
# 1. Install dependencies
cd frontend && npm install

# 2. Start dev server (defaults to port 3000)
npm run dev

# 3. Run component tests
npm test
```
The frontend expects the backend API at `http://localhost:8000` (configurable in `frontend/src/lib/api.ts`).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js Frontend (port 3000)                               │
│                                                             │
│  Chat UI ←── API Client (axios) ──→ GET/POST /api/v1/*     │
└────────────────────────────────┬────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────┐
│  FastAPI Application (port 8000)                            │
│                                                             │
│  Routes ──→ Services ──→ Repositories ──→ PostgreSQL        │
│     │          │                                            │
│     │          └──→ UsersNlQueryService ──→ OpenRouter LLM  │
│     │                       │                               │
│     │                       └──→ query_users_tool ──→ DB    │
│     │                                                       │
│     └──→ Pydantic Schemas (validation)                      │
└─────────────────────────────────────────────────────────────┘
```



### Layers

- **Frontend** (`frontend/`) - Next.js 16 + React 19 chat UI with Tailwind CSS
- **Routes** (`app/api/v1/routes/`) - HTTP endpoints, request/response handling
- **Schemas** (`app/api/v1/schemas/`) - Pydantic models for validation
- **Services** (`app/services/`) - Business logic orchestration
- **Repositories** (`app/repositories/`) - Database access (async SQLAlchemy)
- **Models** (`app/models/entities/`) - SQLAlchemy ORM models
- **Agents** (`agents/`) - AI agent tools and specialist definitions

## Project Structure

```
api-test/
├── app/                              # FastAPI application
│   ├── main.py                       # Entry point, middleware, exception handlers
│   ├── api/v1/
│   │   ├── router.py                 # API router aggregation
│   │   ├── routes/
│   │   │   ├── users.py              # CRUD endpoints for users
│   │   │   ├── agents.py             # Natural language query endpoint
│   │   │   └── health.py             # Health/readiness checks
│   │   └── schemas/
│   │       ├── user_schemas.py       # Request/response models for users
│   │       └── agent_schemas.py      # Request/response models for NL queries
│   ├── config/
│   │   ├── settings.py               # Environment configuration
│   │   └── database.py               # Async SQLAlchemy engine/session
│   ├── core/
│   │   └── exceptions.py             # Custom exception classes
│   ├── models/entities/
│   │   ├── base.py                   # DeclarativeBase + TimestampMixin
│   │   └── user.py                   # User ORM model
│   ├── repositories/
│   │   ├── base.py                   # Generic async CRUD operations
│   │   └── user_repository.py        # User-specific queries
│   └── services/
│       ├── default_nl_query_service.py  # Base NL query service (sessions, keys)
│       ├── user_service.py              # User business logic
│       └── users_nl_query_service.py    # NL query orchestration
├── agents/                           # Google ADK agent definitions
│   ├── shared/
│   │   └── schemas.py                # Agent I/O schemas (UserPublic, UsersQueryResult)
│   ├── tools/
│   │   └── user_query_tools.py       # Read-only DB access tool for agents
│   └── specialists/
│       └── users_query_agent.py      # ADK Agent definition
├── frontend/                         # Next.js chat UI
│   ├── src/
│   │   ├── app/                      # Next.js app router (page, layout)
│   │   ├── components/               # ChatWindow, InputArea, MessageBubble, MessageList
│   │   └── lib/                      # API client (axios), session management
│   └── __tests__/                    # Jest + React Testing Library tests
├── e2e/                              # Playwright end-to-end tests
│   └── chat.spec.ts                  # Chat UI e2e test scenarios
├── scripts/                          # Utility scripts
│   ├── create_user.sh                # Create user via API
│   ├── query_users_nl.sh             # Query users via natural language
│   ├── test_multi_turn.sh            # Test multi-turn conversations
│   ├── check_google_key.sh           # Validate Google API key
│   └── check_llm_key.sh              # Validate OpenRouter & Google API keys
├── alembic/
│   └── versions/                     # Database migration files
├── tests/
│   ├── conftest.py                   # Shared fixtures (db_session, client, user_data)
│   ├── unit/                         # Unit tests
│   └── integration/                  # Integration tests (API endpoints)
└── pyproject.toml                    # Dependencies, tool config
```

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root message |
| GET | `/health` | Health check |
| GET | `/api/v1/health` | Health check (v1) |
| GET | `/api/v1/health/ready` | Readiness check |

### Users CRUD

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/users/` | Create user |
| GET | `/api/v1/users/{id}` | Get user by ID |
| GET | `/api/v1/users/` | List users (with pagination) |
| PATCH | `/api/v1/users/{id}` | Update user fields |
| DELETE | `/api/v1/users/{id}` | Soft delete (sets `is_active=false`) |

### AI Agent

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/agents/users/query` | Natural language user query |

### curl Examples

```bash
# Create a user
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "username": "alice",
    "password": "Password123!",
    "first_name": "Alice",
    "last_name": "Smith"
  }'

# Get user by ID
curl "http://localhost:8000/api/v1/users/1"

# List all users
curl "http://localhost:8000/api/v1/users/"

# List active users only
curl "http://localhost:8000/api/v1/users/?active_only=true"

# Update user
curl -X PATCH "http://localhost:8000/api/v1/users/1" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Alice", "email": "alice.new@example.com"}'

# Delete user (soft delete)
curl -X DELETE "http://localhost:8000/api/v1/users/1"

# AI query - list users
curl -X POST "http://localhost:8000/api/v1/agents/users/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "show me all users", "provider": "openrouter"}'

# AI query - find by email
curl -X POST "http://localhost:8000/api/v1/agents/users/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "find user with email alice@example.com", "provider": "openrouter"}'

# AI query - list active users
curl -X POST "http://localhost:8000/api/v1/agents/users/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "list all active users", "provider": "openrouter"}'
```

## Database Schema

### users table

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key, auto-increment |
| email | String(255) | Unique, not null, indexed |
| username | String(100) | Unique, not null, indexed |
| password | String(100) | Not null (plain text - learning only) |
| first_name | String(100) | Not null |
| last_name | String(100) | Not null |
| is_active | Boolean | Default `true` |
| created_at | DateTime | Auto-set on creation |
| updated_at | DateTime | Auto-set on creation and update |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password1234@localhost:5432/api_test` | PostgreSQL connection string |
| `DATABASE_POOL_SIZE` | `20` | Connection pool size |
| `DATABASE_MAX_OVERFLOW` | `10` | Max overflow connections |
| `OPENROUTER_API_KEY` | *(optional)* | OpenRouter API key for AI queries |
| `OPENROUTER_MODEL` | `deepseek/deepseek-chat` | OpenRouter model name |
| `USERS_NL_DEFAULT_LIMIT` | `20` | Default max users returned by NL query |
| `USERS_NL_MAX_LIMIT` | `100` | Hard cap on NL query results |
| `GOOGLE_API_KEY` | *(optional)* | Google Gemini API key (alternative provider) |
| `GOOGLE_ADK_MODEL` | `gemini-2.0-flash` | Google ADK model name |
| `SECRET_KEY` | `your-secret-key-here` | JWT secret key (auth not yet implemented) |
| `ALGORITHM` | `HS256` | JWT algorithm (auth not yet implemented) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiration (auth not yet implemented) |
| `DEBUG` | `false` | Enable debug mode |

## Development

### Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy .

# All checks
ruff check . && ruff format --check . && mypy .
```

### Testing

```bash
# Run all backend tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run specific test
pytest -k "test_create_user_success" -v
```

### E2E Tests (Playwright)

End-to-end tests for the frontend chat UI are in `e2e/`:

```bash
# Install Playwright browsers (one-time)
npx playwright install

# Run e2e tests (requires both backend and frontend running)
npx playwright test

# Run with UI
npx playwright test --ui
```

### Database Migrations

```bash
# Create new migration from model changes
alembic revision --autogenerate -m "description"

# Apply pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current
```

## Scripts

Several utility scripts are available in the `scripts/` directory:

### Create User
```bash
./scripts/create_user.sh "alice@example.com" "alice" "Password123!" "Alice" "Smith"
```

### Natural Language Query
```bash
./scripts/query_users_nl.sh "show me all users"
./scripts/query_users_nl.sh "find user with email alice@example.com"
```

### Test Multi-turn Conversations
```bash
./scripts/test_multi_turn.sh
```

## Natural Language Query System

The NL query endpoint (`POST /api/v1/agents/users/query`) uses Google ADK agents to convert natural language into structured database queries.

### Supported Queries

- List all users: `"show me all users"`
- Find by email: `"find user with email alice@example.com"`
- List active users: `"list all active users"`
- Get by ID: `"get user with id 1"`

### Response Format

```json
{
  "intent": "list_users",
  "summary": "Found 5 user(s).",
  "data": [{ "id": 1, "email": "...", "username": "...", ... }],
  "filters": { "active_only": false, "skip": 0, "limit": 20, "provider": "openrouter" },
  "count": 5,
  "error": null,
  "session_id": "uuid-here"
}
```

### Intent Values

| Intent | Description |
|--------|-------------|
| `list_users` | Listed all users |
| `list_active_users` | Listed active users only |
| `get_user_by_id` | Found user by ID |
| `get_user_by_email` | Found user by email |
| `get_user_by_username` | Found user by username |
| `clarification_needed` | Query is ambiguous |
| `out_of_scope` | Query is not a read-only users query |

### Session Continuity

Pass `session_id` in subsequent requests to continue a conversation:

```json
{
  "query": "only active ones",
  "session_id": "previous-session-uuid",
  "provider": "openrouter"
}
```

Sessions expire after 5 minutes of inactivity.

## Validation Rules

### Username
- Must start with a letter
- Letters, numbers, and underscores only
- 3-30 characters

### Password
- At least 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character: `!@#$%^&*()_+-=`

### Names (first/last)
- Letters, hyphens, and apostrophes only
- Max 50 characters

## Project Purpose

This project demonstrates:
1. FastAPI application scaffolding with controller-service-repository pattern
2. Google Agent Development Kit (ADK) integration for natural language queries
3. Async SQLAlchemy with PostgreSQL
4. Python 3.12+ type hints and modern tooling

## Security Notes

- **Passwords stored in plain text** - for learning purposes only
- **CORS allows all origins** - not suitable for production
- **NL agent is read-only** - cannot create, update, or delete users
- **No authentication yet** - endpoints are open; JWT settings exist in config but are not wired up
- **Logging not yet implemented** - `structlog` is a dependency but `print()` is currently used instead

## License

MIT
