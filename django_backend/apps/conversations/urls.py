from django.urls import path

from . import views

urlpatterns = [
    path("", views.list_sessions, name="conversation-list"),
    path("<str:session_id>/", views.session_detail, name="conversation-detail"),
    path("<str:session_id>/escalate/", views.escalate_session, name="conversation-escalate"),
    path("<str:session_id>/complete/", views.complete_session, name="conversation-complete"),
]
