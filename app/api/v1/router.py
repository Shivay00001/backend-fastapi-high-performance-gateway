from fastapi import APIRouter
from app.api.v1.endpoints import proxy, cache_demo

api_router = APIRouter()
api_router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])
api_router.include_router(cache_demo.router, prefix="/cache", tags=["cache"])
