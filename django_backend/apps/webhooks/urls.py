from django.urls import path

from . import views

urlpatterns = [
    path("whatsapp/", views.whatsapp_webhook, name="whatsapp-webhook"),
    path("whatsapp/dev/", views.whatsapp_dev_webhook, name="whatsapp-dev-webhook"),
]
