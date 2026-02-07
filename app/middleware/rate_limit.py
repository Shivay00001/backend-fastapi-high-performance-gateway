import redis.asyncio as redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger

class RedisRateLimiter:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

    async def check_limit(self, key: str, limit: int, window: int = 60) -> bool:
        """
        Returns True if request is allowed, False if limit exceeded.
        Uses a sliding window counter or simple fixed window.
        """
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window)
            
            return current <= limit
        except Exception as e:
            logger.error(f"Redis error: {e}")
            # Fail open if Redis is down
            return True

rate_limiter = RedisRateLimiter()

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        is_allowed = await rate_limiter.check_limit(key, settings.RATE_LIMIT_PER_MINUTE)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(status_code=429, detail="Too Many Requests")
            
        return await call_next(request)
