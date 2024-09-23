"""A small in-memory sliding-window rate limiter exposed as a FastAPI dependency.

Suitable for single-process deployments and local development. For multi-instance
production deployments, swap the storage for Redis - the interface stays the same.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import RateLimitedError


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Record a hit and return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            cutoff = now - window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = int(bucket[0] + window_seconds - now) + 1
                return False, max(retry_after, 1)
            bucket.append(now)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, limit: int | None = None) -> Callable[[Request], None]:
    """Build a dependency that limits calls per client IP for the given scope."""

    def dependency(request: Request) -> None:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return
        max_requests = limit or settings.rate_limit_requests
        key = f"{scope}:{_client_key(request)}"
        allowed, retry_after = limiter.check(key, max_requests, settings.rate_limit_window_seconds)
        if not allowed:
            raise RateLimitedError(
                f"Rate limit exceeded for {scope}. Try again in {retry_after}s.",
                retry_after=retry_after,
            )

    return dependency
