"""WhatsApp Business Cloud API client."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self) -> None:
        self.api_url = settings.WHATSAPP_API_URL.rstrip("/")
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    async def send_text_message(self, to_phone: str, text: str) -> dict[str, Any]:
        if not self.is_configured:
            logger.info("WhatsApp not configured; would send to %s: %s", to_phone, text[:200])
            return {"status": "skipped", "reason": "whatsapp_not_configured"}

        to = to_phone.lstrip("+")
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:500] if exc.response is not None else ""
                logger.error(
                    "WhatsApp send failed status=%s body=%s",
                    exc.response.status_code if exc.response else "?",
                    body,
                )
                return {
                    "status": "error",
                    "http_status": exc.response.status_code if exc.response else None,
                    "detail": body,
                }
            except httpx.HTTPError as exc:
                logger.exception("WhatsApp send request failed")
                return {"status": "error", "detail": str(exc)}


def get_whatsapp_client() -> WhatsAppClient:
    return WhatsAppClient()
