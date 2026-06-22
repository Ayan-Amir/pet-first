"""Log inbound HTTP requests (helps debug Meta/ngrok webhooks)."""

from __future__ import annotations

import logging

logger = logging.getLogger("petsfirst.http")


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith(("/api/webhook", "/api/webhooks", "/api/whatsapp")):
            logger.info(
                "Incoming %s %s from %s",
                request.method,
                path,
                request.META.get("HTTP_X_FORWARDED_FOR")
                or request.META.get("REMOTE_ADDR"),
            )
        return self.get_response(request)
