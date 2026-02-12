"""
Global exception handlers.

Ensures consistent error responses and
automatic inclusion of request_id.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


def _request_id(request: Request) -> str | None:
    # Extrai request_id do state, se existir
    return getattr(request.state, "request_id", None)


async def http_exception_handler(request: Request, exc: HTTPException):
    # Tratamento padronizado para erros HTTP conhecidos
    rid = _request_id(request)

    payload = {"detail": exc.detail}
    if rid:
        payload["request_id"] = rid

    return JSONResponse(status_code=exc.status_code, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception):
    # Tratamento para erros não capturados (500)
    rid = _request_id(request)

    payload = {"detail": "internal_error"}
    if rid:
        payload["request_id"] = rid

    # Aqui pode adicionar logging estruturado depois
    return JSONResponse(status_code=500, content=payload)