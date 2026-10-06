"""
Lightweight in-memory sliding-window rate limiter for auth endpoints.

Sufficient for local/dev and single-process deployments. In production this is
replaced by a Redis-backed limiter so limits are shared across workers
(tracked for a later phase).
"""
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import AppError

_hits: "dict[str, deque]" = defaultdict(deque)


class RateLimiter:
    def __init__(self, max_requests: Optional[int] = None, window_seconds: Optional[int] = None, *, scope: str = "auth"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.scope = scope

    async def __call__(self, request: Request) -> None:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return
        max_req = self.max_requests or settings.rate_limit_auth_max
        window = self.window_seconds or settings.rate_limit_auth_window_seconds

        client_ip = request.client.host if request.client else "unknown"
        key = f"{self.scope}:{client_ip}"
        now = time.monotonic()
        bucket = _hits[key]
        while bucket and (now - bucket[0]) > window:
            bucket.popleft()
        if len(bucket) >= max_req:
            raise AppError(
                "Too many requests. Please slow down and try again shortly.",
                code="rate_limited",
                status_code=429,
            )
        bucket.append(now)


def reset_rate_limits() -> None:
    """Test helper — clear all buckets."""
    _hits.clear()
