from apps.webhooks.verification import verify_signature, verify_webhook_subscription


def test_webhook_health_get(client):
    response = client.get("/api/whatsapp/callback/")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"


from apps.webhooks.verification import verify_signature, verify_webhook_subscription


def test_webhook_subscription(settings):
    settings.WHATSAPP_VERIFY_TOKEN = "secret"
    assert verify_webhook_subscription("subscribe", "secret", "12345") == "12345"
    assert verify_webhook_subscription("subscribe", "wrong", "12345") is None


def test_signature_verification(settings):
    settings.WHATSAPP_APP_SECRET = "mysecret"
    body = b'{"hello":"world"}'
    import hashlib
    import hmac

    digest = hmac.new(b"mysecret", body, hashlib.sha256).hexdigest()
    assert verify_signature(body, f"sha256={digest}") is True
    assert verify_signature(body, "sha256=deadbeef") is False
