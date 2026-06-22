"""Pydantic AI agent and shared dependencies."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent

from clients.mcp_client import MCPClient, get_mcp_client


def build_agent_model():
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model_name = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if api_key:
        try:
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider

            provider = OpenAIProvider(base_url=base_url, api_key=api_key)
            return OpenAIModel(model_name, provider=provider)
        except ImportError:
            pass
        try:
            from pydantic_ai.models.openai import OpenAIModel

            return OpenAIModel(model_name, base_url=base_url, api_key=api_key)
        except TypeError:
            pass
    return "test"


@dataclass
class AgentDeps:
    phone: str
    user: dict[str, Any]
    session: dict[str, Any] = field(default_factory=dict)
    mcp: MCPClient = field(default_factory=get_mcp_client)


SYSTEM_PROMPT = """You are a helpful WhatsApp AI assistant for PetsFirst pet clinic.

You help users:
- Book, reschedule, and cancel appointments
- Find clinic services and available time slots
- Answer questions about services, prices, and policies
- Provide information about their pets and appointments

Always be warm, friendly, and professional. Use pet names when available.
For Arabic users, respond in Arabic.

Use the provided tools when you need live data from the clinic systems or the FAQ knowledge base.
If the user asks to speak to a human, acknowledge and say a team member will follow up."""

agent = Agent(
    build_agent_model(),
    deps_type=AgentDeps,
    system_prompt=SYSTEM_PROMPT,
)
