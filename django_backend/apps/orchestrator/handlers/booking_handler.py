"""Flow-specific hooks after agent response."""

from __future__ import annotations

from apps.conversations.models import ConversationSession


def apply_booking_hints(session: ConversationSession, message: str) -> None:
    if "book" in message.lower():
        session.active_flow = ConversationSession.FlowType.BOOKING


def apply_handoff_if_requested(session: ConversationSession, response: str) -> None:
    lowered = response.lower()
    if "human" in lowered or "agent" in lowered or "team member" in lowered:
        session.is_escalated = True
        session.status = ConversationSession.Status.ESCALATED
