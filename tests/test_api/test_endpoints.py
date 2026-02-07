import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_proxy_forward(client: AsyncClient):
    # We mock the external call or test against a known public API (carefully)
    # Here we expect a simple validation error or 502 if upstream fails, 
    # but the endpoint logic is what we test.
    payload = {
        "url": "https://httpbin.org/get",
        "method": "GET"
    }
    response = await client.post(f"{settings.API_V1_STR}/proxy/forward", json=payload)
    # If network is available, 200. If not, 502.
    assert response.status_code in [200, 502]
