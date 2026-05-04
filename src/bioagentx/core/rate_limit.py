import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    """Per-process token-window limiter. Put Redis/API gateway in front for multi-replica prod."""

    def __init__(self, app, limit_per_minute: int, burst: int) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.limit = limit_per_minute
        self.burst = burst
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self._hits[client]
        while window and window[0] < now - 60:
            window.popleft()
        allowed = min(self.limit, self.burst)
        if len(window) >= allowed:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "message": "Too many BioAgentX requests."},
            )
        window.append(now)
        return await call_next(request)
