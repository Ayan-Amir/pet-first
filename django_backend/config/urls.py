from django.contrib import admin
from django.urls import include, path

from apps.webhooks.views import whatsapp_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/webhooks/", include("apps.webhooks.urls")),
    path("api/whatsapp/callback/", whatsapp_webhook, name="whatsapp-meta-callback"),
    path("api/knowledge/", include("apps.knowledge.urls")),
    path("api/conversations/", include("apps.conversations.urls")),
]
