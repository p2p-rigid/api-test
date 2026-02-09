import json
import os
import re
from typing import Any, Literal, cast

import requests
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.utils.context_utils import Aclosing
from google.genai import types

from agents.shared.schemas import UsersQueryResult
from agents.specialists.users_query_agent import users_query_agent
from agents.tools.user_query_tools import query_users_tool
from app.config.settings import settings

Provider = Literal["google", "openrouter"]


class UsersNlQueryService:
    """Orchestrates natural-language users queries across supported providers."""

    def __init__(self) -> None:
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            app_name="users_query_app",
            agent=users_query_agent,
            session_service=self._session_service,
        )

    async def query_users(
        self,
        query: str,
        limit: int | None = None,
        provider: Provider = "google",
    ) -> UsersQueryResult:
        """Execute natural-language user query and return structured result."""

        if provider == "openrouter":
            return await self._query_users_openrouter(query=query, limit=limit)
        return await self._query_users_google(query=query, limit=limit)

    async def _query_users_google(self, query: str, limit: int | None = None) -> UsersQueryResult:
        self._ensure_google_api_key()

        session = await self._session_service.create_session(
            app_name="users_query_app",
            user_id="api_user",
        )

        content = types.Content(role="user", parts=[types.Part(text=query)])
        latest_text = ""
        tool_payload: dict[str, Any] | None = None

        async with Aclosing(
            self._runner.run_async(
                user_id=session.user_id,
                session_id=session.id,
                new_message=content,
            )
        ) as events:
            async for event in events:
                if event.content and event.content.parts:
                    text_parts = [part.text for part in event.content.parts if part.text]
                    if text_parts:
                        latest_text = "".join(text_parts)

                    for part in event.content.parts:
                        if part.function_response and isinstance(part.function_response.response, dict):
                            tool_payload = part.function_response.response

        if tool_payload is not None:
            result = UsersQueryResult.model_validate(tool_payload)
            if not result.summary and latest_text:
                result.summary = latest_text
            return result

        if latest_text:
            return self._result_from_text(latest_text, limit)

        return UsersQueryResult(
            intent="clarification_needed",
            summary="I could not produce a query result.",
            error="No tool output received from agent run.",
        )

    async def _query_users_openrouter(self, query: str, limit: int | None = None) -> UsersQueryResult:
        api_key = self._ensure_openrouter_api_key()

        plan = self._build_openrouter_plan(query=query, api_key=api_key, limit=limit)
        if isinstance(plan, UsersQueryResult):
            return plan

        if limit is not None and "limit" not in plan:
            plan["limit"] = limit

        tool_result = await query_users_tool(**plan)
        return UsersQueryResult.model_validate(tool_result)

    def _build_openrouter_plan(
        self,
        *,
        query: str,
        api_key: str,
        limit: int | None,
    ) -> dict[str, Any] | UsersQueryResult:
        system_prompt = (
            "Convert the user request into a JSON object for a read-only users query tool. "
            "Allowed lookup_type values: id, email, username, list. "
            "Only include these keys: lookup_type, user_id, email, username, active_only, skip, limit. "
            "If request is outside read-only users queries, return exactly: "
            '{"intent":"out_of_scope","summary":"Read-only users query endpoint.","data":[],"filters":{},"count":0,"error":null}. '
            "For ambiguous requests, return exactly: "
            '{"intent":"clarification_needed","summary":"Please clarify your users query.","data":[],"filters":{},"count":0,"error":null}. '
            "Otherwise return only a single JSON object for tool args."
        )

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"query={query}\nlimit={limit if limit is not None else 'null'}",
                    },
                ],
            },
            timeout=20,
        )

        if response.status_code >= 400:
            return UsersQueryResult(
                intent="clarification_needed",
                summary="OpenRouter request failed.",
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            return UsersQueryResult(
                intent="clarification_needed",
                summary="OpenRouter returned an invalid response.",
                error=str(exc),
            )

        parsed = self._parse_json_content(content)
        if parsed is None:
            return UsersQueryResult(
                intent="clarification_needed",
                summary="Could not parse OpenRouter response.",
                error="Expected JSON object in model output.",
            )

        if "intent" in parsed:
            try:
                return UsersQueryResult.model_validate(parsed)
            except Exception as exc:
                return UsersQueryResult(
                    intent="clarification_needed",
                    summary="Invalid structured response from OpenRouter.",
                    error=str(exc),
                )

        return cast(dict[str, Any], parsed)

    def _parse_json_content(self, content: str) -> dict[str, Any] | None:
        stripped = content.strip()
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed
        except ValueError:
            pass

        fenced_match = re.search(r"```(?:json)?\\s*(\{.*?\})\\s*```", stripped, re.DOTALL)
        if fenced_match:
            try:
                parsed = json.loads(fenced_match.group(1))
                if isinstance(parsed, dict):
                    return parsed
            except ValueError:
                return None

        return None

    def _result_from_text(self, text: str, limit: int | None) -> UsersQueryResult:
        lowered = text.lower()
        if "out_of_scope" in lowered or "out of scope" in lowered:
            intent = "out_of_scope"
        elif "clarification" in lowered or "more detail" in lowered:
            intent = "clarification_needed"
        else:
            intent = "clarification_needed"

        return UsersQueryResult(
            intent=intent,
            summary=text,
            filters={"limit": limit} if limit is not None else {},
        )

    def _ensure_google_api_key(self) -> None:
        key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
        if not key or key == "your-google-api-key-here":
            raise RuntimeError("GOOGLE_API_KEY is required for users NL query endpoint")

        os.environ["GOOGLE_API_KEY"] = key

    def _ensure_openrouter_api_key(self) -> str:
        key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is required when provider=openrouter")
        return key


users_nl_query_service = UsersNlQueryService()


async def get_users_nl_query_service() -> UsersNlQueryService:
    """Dependency provider for NL users query service."""

    return users_nl_query_service
