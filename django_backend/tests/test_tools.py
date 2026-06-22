import pytest
from unittest.mock import AsyncMock, patch

from apps.orchestrator.tools.user_lookup import get_user_by_phone


@pytest.mark.asyncio
async def test_get_user_by_phone_delegates_to_client():
    mock_client = AsyncMock()
    mock_client.get_user_by_phone.return_value = {"id": 1}
    user = await get_user_by_phone("971500000000", client=mock_client)
    assert user == {"id": 1}
    mock_client.get_user_by_phone.assert_awaited_once_with("971500000000")
