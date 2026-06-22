"""Knowledge base RAG tool."""

from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async

from apps.knowledge.services.rag_service import search_knowledge_entries
from apps.orchestrator.services.ai_agent import agent


@agent.tool
async def search_knowledge(ctx, query: str, limit: int = 3) -> list[dict[str, Any]]:
    """Search FAQ knowledge base using vector similarity (RAG)."""
    return await sync_to_async(search_knowledge_entries)(query, limit=limit)
