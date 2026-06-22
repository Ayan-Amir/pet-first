"""WhatsApp webhook verification helpers."""

from __future__ import annotations

import hashlib
import hmac
import os

from django.conf import settings


def verify_webhook_subscription(mode: str | None, token: str | None, challenge: str | None) -> str | None:
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return challenge
    return None


def verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if settings.DEBUG and os.getenv("WHATSAPP_SKIP_SIGNATURE_VERIFY", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return True

    secret = settings.WHATSAPP_APP_SECRET
    if not secret:
        return True
    if not signature_header:
        return False
    expected_prefix = "sha256="
    if not signature_header.startswith(expected_prefix):
        return False
    received = signature_header[len(expected_prefix) :]
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, received)
