import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from tests.conftest import requires_postgres


@requires_postgres
@pytest.mark.django_db
def test_knowledge_search_requires_query():
    client = APIClient()
    url = reverse("knowledge-search")
    response = client.get(url)
    assert response.status_code == 400


@requires_postgres
@pytest.mark.django_db
def test_conversation_escalate_not_found():
    client = APIClient()
    url = reverse("conversation-escalate", kwargs={"session_id": "missing"})
    response = client.post(url, {"reason": "user_request"}, format="json")
    assert response.status_code == 404
