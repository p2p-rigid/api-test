import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.users_nl_query_service import get_users_nl_query_service


class _FakeNlService:
    async def query_users(self, query: str, limit: int | None = None, provider: str = "google"):
        if "create" in query.lower():
            return type(
                "Result",
                (),
                {
                    "summary": "Read-only endpoint.",
                    "intent": "out_of_scope",
                    "data": [],
                    "filters": {"limit": limit, "provider": provider},
                    "count": 0,
                    "error": None,
                    "model_dump": lambda self, mode="json": {
                        "summary": self.summary,
                        "intent": self.intent,
                        "data": self.data,
                        "filters": self.filters,
                        "count": self.count,
                        "error": self.error,
                    },
                },
            )()

        return type(
            "Result",
            (),
            {
                "summary": "Found 1 user(s).",
                "intent": "get_user_by_email",
                "data": [
                    {
                        "id": 1,
                        "email": "test@example.com",
                        "username": "testuser",
                        "first_name": "Test",
                        "last_name": "User",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00",
                    }
                ],
                "filters": {"email": "test@example.com", "limit": limit, "provider": provider},
                "count": 1,
                "error": None,
                "model_dump": lambda self, mode="json": {
                    "summary": self.summary,
                    "intent": self.intent,
                    "data": self.data,
                    "filters": self.filters,
                    "count": self.count,
                    "error": self.error,
                },
            },
        )()


@pytest.fixture
async def nl_client():
    async def _provider():
        return _FakeNlService()

    app.dependency_overrides[get_users_nl_query_service] = _provider
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_users_nl_query_service, None)


@pytest.mark.asyncio
async def test_users_nl_query_api_success(nl_client: AsyncClient):
    response = await nl_client.post(
        "/api/v1/agents/users/query",
        json={"query": "find user with email test@example.com", "limit": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "get_user_by_email"
    assert data["count"] == 1
    assert data["filters"]["limit"] == 10
    assert data["filters"]["provider"] == "google"


@pytest.mark.asyncio
async def test_users_nl_query_api_out_of_scope(nl_client: AsyncClient):
    response = await nl_client.post(
        "/api/v1/agents/users/query",
        json={"query": "create a user for me"},
    )

    assert response.status_code == 200
    assert response.json()["intent"] == "out_of_scope"


@pytest.mark.asyncio
async def test_users_nl_query_api_openrouter_provider(nl_client: AsyncClient):
    response = await nl_client.post(
        "/api/v1/agents/users/query",
        json={"query": "list users", "provider": "openrouter"},
    )

    assert response.status_code == 200
    assert response.json()["filters"]["provider"] == "openrouter"
