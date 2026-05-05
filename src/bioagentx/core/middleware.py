import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Injects a unique ``x-trace-id`` header and measures request latency."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        incoming = request.headers.get("x-trace-id")
        try:
            trace_id = str(uuid.UUID(incoming)) if incoming else str(uuid.uuid4())
        except (TypeError, ValueError):
            trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["x-trace-id"] = trace_id
        response.headers["x-process-time-ms"] = f"{(time.perf_counter() - start) * 1000:.2f}"
        return response
