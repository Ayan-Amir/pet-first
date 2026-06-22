from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.knowledge.models import KnowledgeEntry
from apps.knowledge.services.rag_service import search_knowledge_entries


@api_view(["GET"])
def search(request: Request) -> Response:
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response(
            {"error": "Query parameter 'q' is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        limit = int(request.query_params.get("limit", "3"))
    except ValueError:
        limit = 3
    limit = max(1, min(limit, 20))
    results = search_knowledge_entries(query, limit=limit)
    return Response({"data": results})


@api_view(["GET"])
def list_entries(request: Request) -> Response:
    qs = KnowledgeEntry.objects.filter(is_active=True)
    category = request.query_params.get("category")
    if category:
        qs = qs.filter(category=category)
    entries = [
        {
            "id": e.id,
            "question": e.question,
            "answer": e.answer,
            "category": e.category,
        }
        for e in qs.order_by("-updated_at")[:100]
    ]
    return Response({"data": entries})


@api_view(["GET"])
def entry_detail(request: Request, entry_id: int) -> Response:
    try:
        entry = KnowledgeEntry.objects.get(pk=entry_id, is_active=True)
    except KnowledgeEntry.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(
        {
            "data": {
                "id": entry.id,
                "question": entry.question,
                "answer": entry.answer,
                "category": entry.category,
            }
        }
    )
