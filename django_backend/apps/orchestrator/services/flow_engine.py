"""High-level flow routing (booking, cancel, FAQ, handoff)."""

from __future__ import annotations

from apps.conversations.models import ConversationSession


def infer_flow_hint(message: str) -> str:
    text = message.lower()
    if any(w in text for w in ("book", "appointment", "schedule")):
        return ConversationSession.FlowType.BOOKING
    if any(w in text for w in ("cancel", "cancellation")):
        return ConversationSession.FlowType.CANCEL
    if any(w in text for w in ("reschedule", "move my appointment")):
        return ConversationSession.FlowType.RESCHEDULE
    if any(w in text for w in ("price", "cost", "policy", "hours", "what is", "?")):
        return ConversationSession.FlowType.FAQ
    return ConversationSession.FlowType.NONE
