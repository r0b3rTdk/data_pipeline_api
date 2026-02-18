"""
Request ID middleware.

- Reads X-Request-Id from client (if provided)
- Generates one if missing
- Stores it in request.state.request_id
- Returns it in response headers
- Adds processing time header (optional)
"""

import time
import uuid
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("app.request")

class RequestIdMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # Início da medição de tempo
        started = time.perf_counter()

        # Usa X-Request-Id do cliente ou gera um novo
        rid = request.headers.get("X-Request-Id")
        if not rid:
            rid = uuid.uuid4().hex  # 32 caracteres

        # Disponível para todo o request lifecycle
        request.state.request_id = rid

        # Continua fluxo da aplicação
        response: Response = await call_next(request)

        # Tempo total de processamento
        duration_ms = int((time.perf_counter() - started) * 1000)

        # Headers de rastreabilidade
        response.headers["X-Request-Id"] = rid
        response.headers["X-Process-Time-Ms"] = str(duration_ms)

        logger.info(
            "request",
            extra={
                "request_id": rid,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "process_time_ms": duration_ms,
                },
            )

        return response