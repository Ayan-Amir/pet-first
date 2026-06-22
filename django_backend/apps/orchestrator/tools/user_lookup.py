"""Direct MCP call before agent runs (not an @agent.tool)."""

from __future__ import annotations

from typing import Any, Optional

from clients.mcp_client import MCPClient, get_mcp_client


async def get_user_by_phone(
    phone: str, client: MCPClient | None = None
) -> Optional[dict[str, Any]]:
    mcp = client or get_mcp_client()
    return await mcp.get_user_by_phone(phone)
