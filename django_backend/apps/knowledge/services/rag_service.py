"""Embedding generation and vector search for RAG."""

from __future__ import annotations

import logging
from typing import Any

import openai
from django.conf import settings
from pgvector.django import CosineDistance

from apps.knowledge.models import KnowledgeEntry

logger = logging.getLogger(__name__)


def _embedding_client() -> openai.OpenAI:
    return openai.OpenAI(
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY or "missing-key",
    )


def generate_embedding(text: str) -> list[float] | None:
    if not text.strip():
        return None
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set; skipping embedding generation")
        return None

    client = _embedding_client()
    response = client.embeddings.create(
        model=settings.OPENROUTER_EMBEDDING_MODEL,
        input=text,
        dimensions=1536,
    )
    return list(response.data[0].embedding)


def search_knowledge_entries(query: str, limit: int = 3) -> list[dict[str, Any]]:
    embedding = generate_embedding(query)
    if embedding is None:
        return _keyword_fallback(query, limit)

    results = (
        KnowledgeEntry.objects.filter(is_active=True, embedding__isnull=False)
        .annotate(similarity=CosineDistance("embedding", embedding))
        .order_by("similarity")[:limit]
    )
    return [
        {
            "question": entry.question,
            "answer": entry.answer,
            "category": entry.category,
            "similarity": float(entry.similarity),
        }
        for entry in results
    ]


def _keyword_fallback(query: str, limit: int) -> list[dict[str, Any]]:
    qs = KnowledgeEntry.objects.filter(is_active=True, question__icontains=query)[
        :limit
    ]
    return [
        {
            "question": entry.question,
            "answer": entry.answer,
            "category": entry.category,
            "similarity": 0.0,
        }
        for entry in qs
    ]
