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


# --- Per-phone-number rate limiter (Threat 2: SMS flooding) ---
# Allows max 10 inbound messages per phone number per 10 minutes.
_phone_limiter = RateLimiter(max_requests=10, window_seconds=600)

SMS_BLOCKED_NUMBERS: set[str] = set()


def check_phone_rate_limit(phone: str) -> None:
    """Raise 429 if phone has exceeded inbound SMS rate limit, or 403 if blocked."""
    if phone in SMS_BLOCKED_NUMBERS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Number is blocked")
    allowed, retry_after = _phone_limiter.is_allowed(phone)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for this number. Retry after {retry_after}s",
            headers={"Retry-After": str(retry_after)},
        )


# --- Simple admin API key (Threat 3: admin account compromise) ---
def verify_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    """Protect sensitive endpoints (simulation, farmer delete, manual alert trigger)."""
    settings = get_settings()
    expected = getattr(settings, "admin_api_key", None)
    if not expected or expected == "change-me":
        # If not configured, block completely to prevent accidental exposure
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin key not configured")
    if x_admin_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")
