"""
Global exception handlers.

Goal:
- Standardize error responses
- Always include request_id (when available)
- Never leak stack traces to clients
"""
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


def _request_id(request: Request) -> str | None:
    # Extrai request_id do state, se existir
    return getattr(request.state, "request_id", None)

async def http_exception_handler(request: Request, exc: HTTPException):
    # Tratamento padronizado para erros HTTP conhecidos
    rid = _request_id(request)

    payload = {
        "detail": exc.detail,
        "code": "HTTP_ERROR"
    }
    if rid:
        payload["request_id"] = rid

    return JSONResponse(status_code=exc.status_code, content=payload)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Tratamento para erros de validação (422)
    rid = _request_id(request)
    payload = {
        "detail": "Validation error",
        "code": "VALIDATION_ERROR",
        "errors": exc.errors(),
    }
    if rid:
        payload["request_id"] = rid

    return JSONResponse(status_code=422, content=payload)

logger = logging.getLogger("app")

async def unhandled_exception_handler(request: Request, exc: Exception):
    # Tratamento para erros não capturados (500)
    rid = _request_id(request)

    logger.exception(
        "Unhandled exception",
        extra={
            "request_id": rid or "",
            "path": request.url.path,
            "method": request.method,
        },
    )

    payload = {
        "detail": "internal_error",
        "code": "INTERNAL_ERROR"
    }
    if rid:
        payload["request_id"] = rid

    # Aqui pode adicionar logging estruturado depois
    return JSONResponse(status_code=500, content=payload)