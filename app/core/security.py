from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        now = time.time()
        entries = self._requests[key]
        while entries and entries[0] <= now - self.window_seconds:
            entries.popleft()
        if len(entries) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (now - entries[0])))
            return False, retry_after
        entries.append(now)
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        settings = get_settings()
        self.limiter = RateLimiter(
            max_requests=settings.rate_limit_max_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/api/v1/health", "/api/v1/ready"} or request.url.path.startswith(
            "/dashboard"
        ):
            return await call_next(request)
        client_host = request.client.host if request.client else "unknown"
        allowed, retry_after = self.limiter.is_allowed(f"{client_host}:{request.url.path}")
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)


async def verify_webhook_token(x_webhook_token: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_webhook_token != settings.sms_webhook_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook token")
