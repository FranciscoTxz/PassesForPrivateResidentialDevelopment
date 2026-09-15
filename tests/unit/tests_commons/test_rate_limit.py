import pytest
from fastapi import HTTPException
from starlette.requests import Request

from commons.rate_limit import InMemoryRateLimiter


def make_request(path: str = "/auth/sign-in", host: str = "1.2.3.4") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "query_string": b"",
        "headers": [],
        "client": (host, 12345),
        "scheme": "http",
        "server": ("testserver", 80),
    }
    return Request(scope)


class TestInMemoryRateLimiter:
    def test_disabled_limiter_allows_everything(self):
        limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60, enabled=False)

        for _ in range(10):
            limiter(make_request())

    def test_allows_requests_up_to_the_limit(self):
        limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)

        for _ in range(3):
            limiter(make_request())

    def test_raises_429_after_limit(self):
        limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        limiter(make_request())
        limiter(make_request())

        with pytest.raises(HTTPException) as exc_info:
            limiter(make_request())

        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers

    def test_buckets_are_per_path(self):
        limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)
        limiter(make_request(path="/auth/sign-in"))
        limiter(make_request(path="/auth/sign-up"))

    def test_buckets_are_per_client(self):
        limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)
        limiter(make_request(host="1.1.1.1"))
        limiter(make_request(host="2.2.2.2"))
