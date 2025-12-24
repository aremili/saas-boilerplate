
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_success(client: AsyncClient):
    """Test the health check endpoint when the database is healthy."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
