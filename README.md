# API Test

API with Google ADK orchestration built with FastAPI and PostgreSQL.

## Features

- FastAPI for high-performance async API
- PostgreSQL with async SQLAlchemy
- Google Agent Development Kit (ADK) for AI orchestration
- Layered architecture (Routes → Services → Repositories)
- Comprehensive testing with pytest
- Type hints and mypy for type safety

## Project Structure

```
api-test/
├── app/                      # Main application
│   ├── api/v1/routes/       # API endpoints
│   ├── config/              # Configuration
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   └── repositories/        # Data access
├── agents/                  # Google ADK agents
├── tests/                   # Test suite
└── migrations/              # Database migrations
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## Development

- Run tests: `pytest`
- Lint code: `ruff check .`
- Format code: `ruff format .`
- Type check: `mypy .`

## License

MIT

##Note:
wsl bash -c "cd /home/robert/work/api-test && source .venv/bin/activate && pip install -r requirements.txt"