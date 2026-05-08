from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import redis
from app.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        try:
            self.redis = redis.from_url(settings.redis_url)
        except Exception:
            self.redis = None

    async def dispatch(self, request: Request, call_next):
        if self.redis and request.client:
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}"
            current = self.redis.get(key)

            if current and int(current) >= self.max_requests:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Try again later.",
                )

            pipe = self.redis.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, self.window_seconds)
            pipe.execute()

        response = await call_next(request)
        return response
