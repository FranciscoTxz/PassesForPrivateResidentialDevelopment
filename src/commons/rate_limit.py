import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Thread-safe sliding-window rate limiter keyed by client IP and path.

    Intended for a single process. For multiple workers use a shared store
    (e.g. Redis) instead.
    """

    def __init__(self, max_requests: int, window_seconds: int, enabled: bool = True):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        client = request.client.host if request.client else "unknown"
        return f"{client}:{request.url.path}"

    def __call__(self, request: Request) -> None:
        if not self.enabled:
            return

        key = self._client_key(request)
        now = time.monotonic()
        threshold = now - self.window_seconds

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= threshold:
                hits.popleft()

            if len(hits) >= self.max_requests:
                retry_after = max(1, int(hits[0] + self.window_seconds - now) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

            hits.append(now)
