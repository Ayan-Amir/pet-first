from __future__ import annotations

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.orchestrator.services.message_processor import process_incoming_message
from apps.webhooks.verification import verify_signature, verify_webhook_subscription

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
async def whatsapp_webhook(request):
    if request.method == "GET":
        challenge = verify_webhook_subscription(
            request.GET.get("hub.mode"),
            request.GET.get("hub.verify_token"),
            request.GET.get("hub.challenge"),
        )
        if challenge is not None:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse(status=403)

    raw = request.body
    if not verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        logger.warning("WhatsApp signature verification failed")
        return JsonResponse({"error": "invalid signature"}, status=403)

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid json"}, status=400)

    messages = _extract_messages(payload)
    results = []
    for phone, text in messages:
        result = await process_incoming_message(phone, text)
        results.append(result)

    return JsonResponse({"status": "success", "results": results})


@csrf_exempt
@require_http_methods(["POST"])
async def whatsapp_dev_webhook(request):
    """Local/dev endpoint: JSON {"phone": "971500000000", "message": "hello"}."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid json"}, status=400)

    phone = payload.get("phone")
    message = payload.get("message")
    if not phone or not message:
        return JsonResponse(
            {"error": "phone and message are required"},
            status=400,
        )

    result = await process_incoming_message(str(phone), str(message))
    status_code = 404 if result.get("status") == "user_not_found" else 200
    return JsonResponse(result, status=status_code)


def _extract_messages(payload: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for msg in value.get("messages") or []:
                if msg.get("type") != "text":
                    continue
                phone = msg.get("from")
                text = (msg.get("text") or {}).get("body")
                if phone and text:
                    out.append((phone, text))
    return out
