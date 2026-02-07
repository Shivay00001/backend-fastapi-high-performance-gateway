import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ProxyRequest(BaseModel):
    url: str
    method: str = "GET"

@router.post("/forward")
async def forward_request(payload: ProxyRequest):
    """
    Demonstrates async forwarding of requests to another service.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(payload.method, payload.url, timeout=5.0)
            return {
                "status": response.status_code,
                "data": response.json() if response.headers.get("content-type") == "application/json" else response.text,
                "headers": dict(response.headers)
            }
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")
