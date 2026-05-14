import json
import os
import re
import time
from typing import Any

from google.adk.sessions import InMemorySessionService

from app.config.settings import settings

SESSION_TTL_SECONDS = 300


class DefaultNlQueryService:
    """Base class for natural-language queries across supported providers."""

    def __init__(self, app_name: str) -> None:
        self._app_name = app_name
        self._session_service = InMemorySessionService()

    async def _get_or_create_session(
        self,
        *,
        user_id: str,
        session_id: str | None,
    ):
        if session_id:
            existing = await self._session_service.get_session(
                app_name=self._app_name,
                user_id=user_id,
                session_id=session_id,
            )
            if existing:
                current_time = time.time()
                if current_time - existing.last_update_time < SESSION_TTL_SECONDS:
                    return existing
        return await self._session_service.create_session(
            app_name=self._app_name,
            user_id=user_id,
        )

    async def _cleanup_expired_sessions(self, *, user_id: str) -> None:
        list_response = await self._session_service.list_sessions(
            app_name=self._app_name,
            user_id=user_id,
        )
        current_time = time.time()
        for session in list_response.sessions:
            if current_time - session.last_update_time >= SESSION_TTL_SECONDS:
                await self._session_service.delete_session(
                    app_name=self._app_name,
                    user_id=user_id,
                    session_id=session.id,
                )

    def _ensure_google_api_key(self) -> None:
        key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
        if not key or key == "your-google-api-key-here":
            raise RuntimeError("GOOGLE_API_KEY is required for NL query endpoint")

        os.environ["GOOGLE_API_KEY"] = key

    def _ensure_openrouter_api_key(self) -> str:
        key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is required when provider=openrouter")
        return key

    def _parse_json_content(self, content: str) -> dict[str, Any] | None:
        stripped = content.strip()
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed
        except ValueError:
            pass

        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
        if fenced_match:
            try:
                parsed = json.loads(fenced_match.group(1))
                if isinstance(parsed, dict):
                    return parsed
            except ValueError:
                return None

        return None
