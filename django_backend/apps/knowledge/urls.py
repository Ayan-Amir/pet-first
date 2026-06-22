from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.search, name="knowledge-search"),
    path("entries/", views.list_entries, name="knowledge-list"),
    path("entries/<int:entry_id>/", views.entry_detail, name="knowledge-detail"),
]
