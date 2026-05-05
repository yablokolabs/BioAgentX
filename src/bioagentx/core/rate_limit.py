import time
from collections import deque
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_PRUNE_INTERVAL = 300
_WINDOW_SECONDS = 60


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter scoped per client IP.

    Allows up to ``burst`` requests in quick succession and enforces
    ``limit_per_minute`` over a rolling 60-second window. Use an API
    gateway or Redis for distributed rate limiting across replicas.
    """

    def __init__(self, app: object, *, limit_per_minute: int, burst: int) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.limit = limit_per_minute
        self.burst = burst
        self._hits: dict[str, deque[float]] = {}
        self._last_prune: float = time.monotonic()

    def _prune_stale_clients(self, now: float) -> None:
        """Remove tracking entries for clients with no recent activity."""
        if now - self._last_prune < _PRUNE_INTERVAL:
            return
        stale = [k for k, v in self._hits.items() if not v or v[-1] < now - _WINDOW_SECONDS]
        for key in stale:
            del self._hits[key]
        self._last_prune = now

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        self._prune_stale_clients(now)

        window = self._hits.setdefault(client, deque())
        while window and window[0] < now - _WINDOW_SECONDS:
            window.popleft()

        # Burst cap prevents instantaneous flooding; the sliding window
        # enforces the sustained rate over the full minute.
        allowed = max(self.burst, self.limit)
        if len(window) >= allowed:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "message": "Too many requests — please retry shortly."},
            )
        window.append(now)
        return await call_next(request)
