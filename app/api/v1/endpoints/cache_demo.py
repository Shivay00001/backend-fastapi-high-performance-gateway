from fastapi import APIRouter, Depends
from app.middleware.rate_limit import rate_limiter
import asyncio

router = APIRouter()

@router.get("/heavy-computation")
async def heavy_computation():
    """
    Simulates a heavy async computation that effectively utilizes
    FastAPI's async capabilities without blocking the event loop.
    """
    await asyncio.sleep(0.5)  # Simulate I/O delay
    return {"result": 42, "message": "Computed asynchronously"}
