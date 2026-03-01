from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.services.users_nl_query_service import UsersNlQueryService


class _FakeSession:
    def __init__(self, uid: str = "u1", sid: str = "s1"):
        self.user_id = uid
        self.id = sid
        self.last_update_time = 0.0


class _ListSessionsResponse:
    def __init__(self, sessions: list[_FakeSession] = None):
        self.sessions = sessions or []


class _FakeSessionService:
    def __init__(self, existing_session: _FakeSession | None = None):
        self._existing_session = existing_session

    async def create_session(self, **_kwargs):
        return _FakeSession()

    async def get_session(self, **_kwargs):
        return self._existing_session

    async def list_sessions(self, **_kwargs):
        return _ListSessionsResponse()

    async def delete_session(self, **_kwargs):
        pass


class _FakeAclosing:
    def __init__(self, agen):
        self._agen = agen

    async def __aenter__(self):
        return self._agen

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeRunner:
    def __init__(self, events: list[Any]):
        self._events = events

    async def run_async(self, **_kwargs):
        for event in self._events:
            yield event


def _event_with_function_response(response: dict[str, Any]):
    part = type("Part", (), {"text": None, "function_response": type("FR", (), {"response": response})()})()
    content = type("Content", (), {"parts": [part]})()
    return type("Event", (), {"content": content})()


def _event_with_text(text: str):
    part = type("Part", (), {"text": text, "function_response": None})()
    content = type("Content", (), {"parts": [part]})()
    return type("Event", (), {"content": content})()


@pytest.mark.asyncio
async def test_query_users_returns_tool_payload(monkeypatch):
    service = UsersNlQueryService()
    service._session_service = _FakeSessionService()  # noqa: SLF001
    service._runner = _FakeRunner(
        [
            _event_with_function_response(
                {
                    "intent": "list_users",
                    "summary": "Found 0 user(s).",
                    "data": [],
                    "filters": {},
                    "count": 0,
                    "error": None,
                }
            )
        ]
    )

    monkeypatch.setattr(
        "app.services.users_nl_query_service.Aclosing",
        lambda agen: _FakeAclosing(agen),
    )
    monkeypatch.setattr("app.services.users_nl_query_service.settings.google_api_key", "dummy")

    result = await service.query_users("list users")

    assert result.intent == "list_users"
    assert result.count == 0
    assert result.session_id is not None


@pytest.mark.asyncio
async def test_query_users_falls_back_to_text(monkeypatch):
    service = UsersNlQueryService()
    service._session_service = _FakeSessionService()  # noqa: SLF001
    service._runner = _FakeRunner([_event_with_text("This is out of scope.")])

    monkeypatch.setattr(
        "app.services.users_nl_query_service.Aclosing",
        lambda agen: _FakeAclosing(agen),
    )
    monkeypatch.setattr("app.services.users_nl_query_service.settings.google_api_key", "dummy")

    result = await service.query_users("delete users")

    assert result.intent == "out_of_scope"
    assert result.session_id is not None


@pytest.mark.asyncio
async def test_query_users_openrouter_executes_tool(monkeypatch):
    service = UsersNlQueryService()

    monkeypatch.setattr("app.services.users_nl_query_service.settings.openrouter_api_key", "or-key")
    monkeypatch.setattr(
        service,
        "_build_openrouter_plan",
        lambda **kwargs: {"lookup_type": "list", "active_only": True, "limit": 3},
    )

    async def _fake_query_users_tool(**kwargs):
        assert kwargs["lookup_type"] == "list"
        assert kwargs["active_only"] is True
        return {
            "intent": "list_active_users",
            "summary": "Found 0 user(s).",
            "data": [],
            "filters": {"active_only": True},
            "count": 0,
            "error": None,
        }

    monkeypatch.setattr("app.services.users_nl_query_service.query_users_tool", _fake_query_users_tool)

    result = await service.query_users("show active users", provider="openrouter")

    assert result.intent == "list_active_users"


@pytest.mark.asyncio
async def test_query_users_with_custom_user_id(monkeypatch):
    service = UsersNlQueryService()
    create_called_with: dict[str, Any] = {}

    class _TrackingSessionService(_FakeSessionService):
        async def create_session(self, **kwargs):
            create_called_with.update(kwargs)
            return _FakeSession(uid=kwargs.get("user_id", "api_user"))

        async def list_sessions(self, **kwargs):
            return _ListSessionsResponse([])

    service._session_service = _TrackingSessionService()  # noqa: SLF001
    service._runner = _FakeRunner(
        [
            _event_with_function_response(
                {
                    "intent": "list_users",
                    "summary": "Found 2 user(s).",
                    "data": [],
                    "filters": {},
                    "count": 2,
                    "error": None,
                }
            )
        ]
    )

    monkeypatch.setattr(
        "app.services.users_nl_query_service.Aclosing",
        lambda agen: _FakeAclosing(agen),
    )
    monkeypatch.setattr("app.services.users_nl_query_service.settings.google_api_key", "dummy")

    result = await service.query_users("list users", user_id="user123")

    assert result.intent == "list_users"
    assert create_called_with.get("user_id") == "user123"


@pytest.mark.asyncio
async def test_query_users_continues_existing_session(monkeypatch):
    import time
    service = UsersNlQueryService()
    existing_session = _FakeSession(uid="user123", sid="existing-session-id")
    existing_session.last_update_time = time.time()

    class _ReuseSessionService(_FakeSessionService):
        def __init__(self):
            super().__init__(existing_session)

        async def get_session(self, **kwargs):
            return existing_session

        async def list_sessions(self, **kwargs):
            return _ListSessionsResponse([existing_session])

        async def create_session(self, **kwargs):
            pytest.fail("create_session should not be called when session_id is provided and valid")

    service._session_service = _ReuseSessionService()  # noqa: SLF001
    service._runner = _FakeRunner(
        [
            _event_with_function_response(
                {
                    "intent": "list_users",
                    "summary": "Found 1 user(s).",
                    "data": [],
                    "filters": {},
                    "count": 1,
                    "error": None,
                }
            )
        ]
    )

    monkeypatch.setattr(
        "app.services.users_nl_query_service.Aclosing",
        lambda agen: _FakeAclosing(agen),
    )
    monkeypatch.setattr("app.services.users_nl_query_service.settings.google_api_key", "dummy")

    result = await service.query_users(
        "list users",
        user_id="user123",
        session_id="existing-session-id",
    )

    assert result.intent == "list_users"
    assert result.session_id == "existing-session-id"


def test_ensure_google_api_key_raises_when_missing(monkeypatch):
    service = UsersNlQueryService()
    monkeypatch.setattr("app.services.users_nl_query_service.settings.google_api_key", None)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(RuntimeError):
        service._ensure_google_api_key()  # noqa: SLF001


def test_ensure_openrouter_api_key_raises_when_missing(monkeypatch):
    service = UsersNlQueryService()
    monkeypatch.setattr("app.services.users_nl_query_service.settings.openrouter_api_key", None)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError):
        service._ensure_openrouter_api_key()  # noqa: SLF001
