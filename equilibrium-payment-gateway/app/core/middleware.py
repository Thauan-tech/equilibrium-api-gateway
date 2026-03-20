import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("equilibrium.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Loga todas as requisições com tempo de resposta e request ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        request.state.request_id = request_id

        logger.info(
            f"→ [{request_id}] {request.method} {request.url.path}"
            + (f"?{request.url.query}" if request.url.query else "")
        )

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        logger.info(f"← [{request_id}] {response.status_code} ({duration_ms:.1f}ms)")

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting simples em memória (use Redis em produção)."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Rotas de health nunca são limitadas
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        timestamps = self._store.get(client_ip, [])
        timestamps = [t for t in timestamps if now - t < self.window_seconds]

        if len(timestamps) >= self.max_requests:
            return Response(
                content='{"detail":"Rate limit excedido. Tente novamente em instantes."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.window_seconds)},
            )

        timestamps.append(now)
        self._store[client_ip] = timestamps

        return await call_next(request)
