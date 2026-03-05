"""
Request tracing middleware.

- Ensures a request correlation id (X-Request-Id)
- Exposes request_id via request.state.request_id
- Adds response headers: X-Request-Id, X-Process-Time-Ms
- Records HTTP/global counters and per-route latency metrics
- Logs request summary with request_id for correlation
"""

import time
import uuid
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.http_metrics import record as record_http
from app.core.http_metrics import record_route

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
        
        # Métricas de HTTP (contagem e classificação por status)
        record_http(response.status_code)

        # Tempo total de processamento
        duration_ms = int((time.perf_counter() - started) * 1000)

        # Headers de rastreabilidade
        response.headers["X-Request-Id"] = rid
        response.headers["X-Process-Time-Ms"] = str(duration_ms)

        # Log de requisição
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Tenta obter a rota para métricas mais precisas, cai para path se nao tiver
        route_obj = request.scope.get("route")
        route_path = getattr(route_obj, "path", request.url.path)

        # Atualiza métricas de rota
        record_route(request.method, route_path, duration_ms)

        # log
        logger.info(
            "request",
            extra={
                "request_id": rid,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "process_time_ms": duration_ms,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": getattr(request.state, "user_id", None),
                "role": getattr(request.state, "role", None),
                },
            )

        return response