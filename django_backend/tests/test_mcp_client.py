import pytest
import respx
from httpx import Response

from clients.mcp_client import MCPClient


@pytest.mark.asyncio
@respx.mock
async def test_get_user_by_phone_registered():
    base = "http://mock.test/api/v1.0/mcp"
    respx.get(f"{base}/users/identifyByPhone/971500000000").mock(
        return_value=Response(200, json={"status": 200, "data": {"id": 893, "name": "Test"}})
    )
    client = MCPClient(base_url=base)
    user = await client.get_user_by_phone("971500000000")
    assert user is not None
    assert user["id"] == 893


@pytest.mark.asyncio
@respx.mock
async def test_get_clinics_retries_then_succeeds():
    base = "http://mock.test/api/v1.0/mcp"
    route = respx.get(f"{base}/clinics")
    route.side_effect = [
        Response(503, json={"error": "down"}),
        Response(200, json={"status": 200, "data": [{"id": 1}]}),
    ]
    client = MCPClient(base_url=base)
    clinics = await client.get_clinics()
    assert len(clinics) == 1
