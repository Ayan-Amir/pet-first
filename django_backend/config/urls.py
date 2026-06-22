from django.contrib import admin
from django.urls import include, path

from apps.webhooks.views import whatsapp_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/webhooks/", include("apps.webhooks.urls")),
    path("api/whatsapp/callback/", whatsapp_webhook, name="whatsapp-meta-callback"),
    # Shorthand alias (singular "webhook")
    path("api/webhook/", whatsapp_webhook, name="whatsapp-webhook-alias"),
    path("api/knowledge/", include("apps.knowledge.urls")),
    path("api/conversations/", include("apps.conversations.urls")),
]
