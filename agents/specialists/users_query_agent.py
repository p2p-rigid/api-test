from google.adk.agents import Agent

from agents.tools.user_query_tools import query_users_tool
from app.config.settings import settings

INSTRUCTION = """
You are a read-only users data assistant.

Rules:
- You may only answer queries about users data.
- You may only use the query_users_tool for database access.
- Never create, update, or delete users.
- If the request asks for mutations, refuse with intent out_of_scope.
- If the request is ambiguous, ask for clarification and return intent clarification_needed.
- Never fabricate results.
""".strip()

users_query_agent = Agent(
    name="users_query_agent",
    description="Read-only natural language query assistant for users",
    model=settings.google_adk_model,
    instruction=INSTRUCTION,
    tools=[query_users_tool],
)
