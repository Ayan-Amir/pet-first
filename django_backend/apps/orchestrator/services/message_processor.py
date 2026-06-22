"""Main message processing pipeline."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

from apps.conversations.models import ConversationSession
from apps.orchestrator.handlers.booking_handler import (
    apply_booking_hints,
    apply_handoff_if_requested,
)
from apps.orchestrator.services.ai_agent import AgentDeps, agent
from apps.orchestrator.services.flow_engine import infer_flow_hint
from apps.orchestrator.services.state_manager import (
    get_or_create_active_session,
    touch_session,
)
from apps.orchestrator.tools import mcp_backend_tools, knowledge_tools  # noqa: F401
from clients.mcp_client import MCPClientError, get_mcp_client
from clients.whatsapp_client import get_whatsapp_client
from apps.orchestrator.tools.user_lookup import get_user_by_phone

logger = logging.getLogger(__name__)


async def process_incoming_message(phone: str, message: str) -> dict[str, Any]:
    phone = phone.lstrip("+").replace("whatsapp:", "")

    try:
        user = await get_user_by_phone(phone)
    except MCPClientError as exc:
        logger.exception("User lookup failed")
        text = "Sorry, we could not reach our booking system. Please try again shortly."
        wa = await get_whatsapp_client().send_text_message(phone, text)
        return {"error": str(exc), "status": "mcp_error", "whatsapp": wa}

    if not user:
        text = (
            "We couldn't find your account. Please register with PetsFirst first "
            "or contact support."
        )
        await get_whatsapp_client().send_text_message(phone, text)
        return {"status": "user_not_found", "response": text}

    session = await get_or_create_active_session(phone)
    session_state = dict(session.collected_data or {})
    session_state["user"] = user

    flow_hint = infer_flow_hint(message)
    if flow_hint != ConversationSession.FlowType.NONE:
        session.active_flow = flow_hint

    deps = AgentDeps(
        phone=phone,
        user=user,
        session=session_state,
        mcp=get_mcp_client(),
    )

    context_prefix = (
        f"User phone: {phone}. User profile: {user}. "
        f"Session state: {session_state}.\n\nUser message: "
    )

    try:
        if settings.OPENROUTER_API_KEY:
            result = await agent.run(context_prefix + message, deps=deps)
            response_text = str(result.output)
            tools_called = _extract_tool_names(result)
        else:
            response_text = (
                "Thanks for your message! Our AI assistant is not fully configured yet, "
                "but we received your request."
            )
            tools_called = []
    except Exception as exc:
        logger.exception("Agent run failed")
        response_text = (
            "Sorry, something went wrong while processing your message. "
            "Please try again in a moment."
        )
        tools_called = []
        session_state["last_error"] = str(exc)

    apply_booking_hints(session, message)
    apply_handoff_if_requested(session, response_text)

    session_state["last_user_message"] = message
    session_state["last_assistant_message"] = response_text
    session_state["tools_called"] = tools_called

    await touch_session(session, session_state)
    await session.asave(
        update_fields=["active_flow", "status", "is_escalated", "updated_at"]
    )

    wa_result = await get_whatsapp_client().send_text_message(phone, response_text)

    return {
        "status": "success",
        "response": response_text,
        "tools_called": tools_called,
        "whatsapp": wa_result,
        "session_id": session.session_id,
    }


def _extract_tool_names(result: Any) -> list[str]:
    names: list[str] = []
    try:
        for msg in result.all_messages():
            for part in getattr(msg, "parts", []) or []:
                tool_name = getattr(part, "tool_name", None)
                if tool_name:
                    names.append(tool_name)
    except Exception:
        pass
    return names
