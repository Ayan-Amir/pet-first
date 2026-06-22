from __future__ import annotations

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import ConversationSession


@api_view(["GET"])
def list_sessions(request: Request) -> Response:
    phone = request.query_params.get("phone")
    qs = ConversationSession.objects.all()
    if phone:
        qs = qs.filter(phone=phone)
    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)
    escalated = request.query_params.get("is_escalated")
    if escalated is not None:
        qs = qs.filter(is_escalated=escalated.lower() in ("1", "true", "yes"))

    sessions = [
        _serialize_session(s)
        for s in qs.order_by("-updated_at")[:100]
    ]
    return Response({"data": sessions})


@api_view(["GET"])
def session_detail(request: Request, session_id: str) -> Response:
    try:
        session = ConversationSession.objects.get(session_id=session_id)
    except ConversationSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"data": _serialize_session(session)})


@api_view(["POST"])
def escalate_session(request: Request, session_id: str) -> Response:
    try:
        session = ConversationSession.objects.get(session_id=session_id)
    except ConversationSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

    reason = request.data.get(
        "reason", ConversationSession.EscalationReason.USER_REQUEST
    )
    context = request.data.get("context") or {}
    if not isinstance(context, dict):
        context = {}

    session.is_escalated = True
    session.status = ConversationSession.Status.ESCALATED
    session.escalation_reason = reason
    session.escalation_context = context
    session.escalated_at = timezone.now()
    session.save(
        update_fields=[
            "is_escalated",
            "status",
            "escalation_reason",
            "escalation_context",
            "escalated_at",
            "updated_at",
        ]
    )
    return Response({"data": _serialize_session(session)})


@api_view(["POST"])
def complete_session(request: Request, session_id: str) -> Response:
    try:
        session = ConversationSession.objects.get(session_id=session_id)
    except ConversationSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

    session.status = ConversationSession.Status.COMPLETED
    session.save(update_fields=["status", "updated_at"])
    return Response({"data": _serialize_session(session)})


def _serialize_session(session: ConversationSession) -> dict:
    return {
        "session_id": session.session_id,
        "phone": session.phone,
        "status": session.status,
        "active_flow": session.active_flow,
        "current_step": session.current_step,
        "collected_data": session.collected_data,
        "is_escalated": session.is_escalated,
        "escalation_reason": session.escalation_reason,
        "escalation_context": session.escalation_context,
        "escalated_at": session.escalated_at.isoformat() if session.escalated_at else None,
        "expires_at": session.expires_at.isoformat(),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
