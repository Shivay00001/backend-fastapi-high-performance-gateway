import pytest
from httpx import AsyncClient
from app.main import app
from app.core.config import settings

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def clear_redis():
    # In a real test env, we would flush a test redis db
    pass
