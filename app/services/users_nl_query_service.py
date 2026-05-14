from typing import Any, Literal, cast

import requests
from google.adk.runners import Runner
from google.adk.utils.context_utils import Aclosing
from google.genai import types

from agents.shared.schemas import UsersQueryResult
from agents.specialists.users_query_agent import users_query_agent
from agents.tools.user_query_tools import query_users_tool
from app.config.settings import settings
from app.services.default_nl_query_service import DefaultNlQueryService

Provider = Literal["google", "openrouter"]

SESSION_TTL_SECONDS = 300


class UsersNlQueryService(DefaultNlQueryService):
    """Orchestrates natural-language users queries across supported providers."""

    def __init__(self) -> None:
        super().__init__("users_query_app")
        self._runner = Runner(
            app_name="users_query_app",
            agent=users_query_agent,
            session_service=self._session_service,
        )

    async def query_users(
        self,
        query: str,
        user_id: str = "api_user",
        session_id: str | None = None,
        limit: int | None = None,
        provider: Provider = "google",
    ) -> UsersQueryResult:
        """Execute natural-language user query and return structured result."""

        if provider == "openrouter":
            return await self._query_users_openrouter(
                query=query, user_id=user_id, session_id=session_id, limit=limit
            )
        return await self._query_users_google(
            query=query, user_id=user_id, session_id=session_id, limit=limit
        )

    async def _query_users_google(
        self,
        query: str,
        user_id: str,
        session_id: str | None,
        limit: int | None = None,
    ) -> UsersQueryResult:
        self._ensure_google_api_key()

        await self._cleanup_expired_sessions(user_id=user_id)

        session = await self._get_or_create_session(
            user_id=user_id,
            session_id=session_id,
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

        result_dict: dict[str, Any]
        if tool_payload is not None:
            result = UsersQueryResult.model_validate(tool_payload)
            if not result.summary and latest_text:
                result.summary = latest_text
            result_dict = result.model_dump()
            result_dict["session_id"] = session.id
            return UsersQueryResult(**result_dict)

        if latest_text:
            result = self._result_from_text(latest_text, limit)
            result_dict = result.model_dump()
            result_dict["session_id"] = session.id
            return UsersQueryResult(**result_dict)

        result = UsersQueryResult(
            intent="clarification_needed",
            summary="I could not produce a query result.",
            error="No tool output received from agent run.",
        )
        result_dict = result.model_dump()
        result_dict["session_id"] = session.id
        return UsersQueryResult(**result_dict)

    async def _query_users_openrouter(
        self,
        query: str,
        user_id: str,
        session_id: str | None,
        limit: int | None = None,
    ) -> UsersQueryResult:
        await self._cleanup_expired_sessions(user_id=user_id)

        session = await self._get_or_create_session(
            user_id=user_id,
            session_id=session_id,
        )

        if not hasattr(self, "_conversation_history"):
            self._conversation_history: dict[str, list[dict[str, str]]] = {}

        history = self._conversation_history.get(session.id, [])

        api_key = self._ensure_openrouter_api_key()

        plan = self._build_openrouter_plan(
            query=query, api_key=api_key, limit=limit, conversation_history=history
        )
        if isinstance(plan, UsersQueryResult):
            return plan

        if limit is not None and "limit" not in plan:
            plan["limit"] = limit

        tool_result = await query_users_tool(**plan)
        result = UsersQueryResult.model_validate(tool_result)

        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": result.summary})
        self._conversation_history[session.id] = history[-10:]

        result_dict = result.model_dump()
        result_dict["session_id"] = session.id
        return UsersQueryResult(**result_dict)

    def _build_openrouter_plan(
        self,
        *,
        query: str,
        api_key: str,
        limit: int | None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any] | UsersQueryResult:
        system_prompt = (
            "You are a JSON generator. Return ONLY valid JSON, no explanations, no examples, no markdown. "
            "Convert the user request into a JSON object for a read-only users query tool. "
            "Allowed lookup_type values: id, email, username, list. "
            "Only include these keys: lookup_type, user_id, email, username, active_only, skip, limit. "
            "If request is outside read-only users queries, return exactly this JSON: "
            "{\"intent\":\"out_of_scope\",\"summary\":\"Read-only users query endpoint.\",\"data\":[],\"filters\":{},\"count\":0,\"error\":null} "
            "For ambiguous requests, return exactly this JSON: "
            "{\"intent\":\"clarification_needed\",\"summary\":\"Please clarify your users query.\",\"data\":[],\"filters\":{},\"count\":0,\"error\":null} "
            "Otherwise return ONLY a single JSON object, nothing else."

        )

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            history_context = "The user is having a conversation about querying users. Previous messages:\n"
            for msg in conversation_history:
                history_context += f"{msg['role'].upper()}: {msg['content']}\n"
            messages.append({"role": "system", "content": history_context})

        messages.append({
            "role": "user",
            "content": f"Current query: {query}\nlimit={limit if limit is not None else 'null'}",
        })

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_model,
                "temperature": 0,
                "messages": messages,
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


users_nl_query_service = UsersNlQueryService()


async def get_users_nl_query_service() -> UsersNlQueryService:
    """Dependency provider for NL users query service."""

    return users_nl_query_service
