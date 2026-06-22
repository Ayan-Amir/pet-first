from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/webhooks/", include("apps.webhooks.urls")),
    path("api/knowledge/", include("apps.knowledge.urls")),
    path("api/conversations/", include("apps.conversations.urls")),
]
