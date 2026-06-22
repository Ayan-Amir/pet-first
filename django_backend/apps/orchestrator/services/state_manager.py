"""Session persistence helpers."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.conversations.models import ConversationSession


async def get_or_create_active_session(phone: str) -> ConversationSession:
    now = timezone.now()
    ttl = timedelta(hours=settings.SESSION_TTL_HOURS)
    try:
        session = await ConversationSession.objects.aget(
            phone=phone,
            status=ConversationSession.Status.ACTIVE,
            expires_at__gt=now,
        )
        return session
    except ConversationSession.DoesNotExist:
        return await ConversationSession.objects.acreate(
            phone=phone,
            session_id=f"{phone}_{uuid.uuid4().hex[:12]}",
            expires_at=now + ttl,
            collected_data={},
        )


async def touch_session(session: ConversationSession, collected_data: dict) -> None:
    session.collected_data = collected_data
    session.updated_at = timezone.now()
    await session.asave(update_fields=["collected_data", "updated_at"])
