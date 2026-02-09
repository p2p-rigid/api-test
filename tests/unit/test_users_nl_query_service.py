from typing import Any

import pytest

from app.services.users_nl_query_service import UsersNlQueryService


class _FakeSession:
    user_id = "u1"
    id = "s1"


class _FakeSessionService:
    async def create_session(self, **_kwargs):
        return _FakeSession()


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
