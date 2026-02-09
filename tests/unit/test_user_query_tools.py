from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from agents.tools.user_query_tools import query_users_tool


class _AsyncSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return None


def _make_user(user_id: int, email: str, username: str, is_active: bool = True) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=user_id,
        email=email,
        username=username,
        first_name="Test",
        last_name="User",
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_query_users_tool_lookup_by_email(monkeypatch):
    class FakeUserService:
        def __init__(self, _db):
            pass

        async def get_user_by_email(self, email: str):
            return _make_user(1, email, "testuser")

    class FakeUserRepository:
        def __init__(self, _db):
            pass

    monkeypatch.setattr("agents.tools.user_query_tools.AsyncSessionLocal", _AsyncSessionContext)
    monkeypatch.setattr("agents.tools.user_query_tools.UserService", FakeUserService)
    monkeypatch.setattr("agents.tools.user_query_tools.UserRepository", FakeUserRepository)

    result = await query_users_tool(lookup_type="email", email="test@example.com")

    assert result["intent"] == "get_user_by_email"
    assert result["count"] == 1
    assert result["data"][0]["email"] == "test@example.com"
    assert "password" not in result["data"][0]


@pytest.mark.asyncio
async def test_query_users_tool_list_active(monkeypatch):
    class FakeUserService:
        def __init__(self, _db):
            pass

        async def get_active_users(self, skip: int, limit: int):
            assert skip == 0
            assert limit == 5
            return [
                _make_user(1, "one@example.com", "one", True),
                _make_user(2, "two@example.com", "two", True),
            ]

    class FakeUserRepository:
        def __init__(self, _db):
            pass

    monkeypatch.setattr("agents.tools.user_query_tools.AsyncSessionLocal", _AsyncSessionContext)
    monkeypatch.setattr("agents.tools.user_query_tools.UserService", FakeUserService)
    monkeypatch.setattr("agents.tools.user_query_tools.UserRepository", FakeUserRepository)

    result = await query_users_tool(lookup_type="list", active_only=True, limit=5)

    assert result["intent"] == "list_active_users"
    assert result["count"] == 2
    assert result["filters"]["active_only"] is True


@pytest.mark.asyncio
async def test_query_users_tool_invalid_input_returns_clarification():
    result = await query_users_tool(lookup_type="id")

    assert result["intent"] == "clarification_needed"
    assert result["error"] is not None


@pytest.mark.asyncio
async def test_query_users_tool_accepts_none_optional_fields(monkeypatch):
    class FakeUserService:
        def __init__(self, _db):
            pass

        async def get_user_by_email(self, email: str):
            return _make_user(2, email, "johndoe")

    class FakeUserRepository:
        def __init__(self, _db):
            pass

    monkeypatch.setattr("agents.tools.user_query_tools.AsyncSessionLocal", _AsyncSessionContext)
    monkeypatch.setattr("agents.tools.user_query_tools.UserService", FakeUserService)
    monkeypatch.setattr("agents.tools.user_query_tools.UserRepository", FakeUserRepository)

    result = await query_users_tool(
        lookup_type="email",
        email="john@example.com",
        active_only=None,
        skip=None,
        limit=None,
    )

    assert result["intent"] == "get_user_by_email"
    assert result["count"] == 1
