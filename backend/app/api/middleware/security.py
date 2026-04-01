from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityMiddleware(BaseHTTPMiddleware):
    """Request correlation + fixed-window rate limiting for sensitive routes."""

    def __init__(self, app, *, max_requests: int, window_seconds: int) -> None:
        super().__init__(app)
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    @staticmethod
    def _identity(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            client = forwarded_for.split(",", 1)[0].strip()
        else:
            client = request.client.host if request.client else "unknown"
        return f"{request.url.path}:{client}"

    @staticmethod
    def _is_exempt(request: Request) -> bool:
        if request.url.path.endswith("/health"):
            return True
        if request.method in {"OPTIONS", "HEAD"}:
            return True
        return False

    def _allow(self, identity: str, now: float) -> bool:
        floor = now - self.window_seconds
        with self._lock:
            q = self._hits[identity]
            while q and q[0] <= floor:
                q.popleft()
            if len(q) >= self.max_requests:
                return False
            q.append(now)
            return True

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        if not self._is_exempt(request):
            if not self._allow(self._identity(request), time.monotonic()):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded", "request_id": request_id},
                    headers={"Retry-After": str(self.window_seconds), "X-Request-ID": request_id},
                )

        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request_id)
        return response
