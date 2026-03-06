"""
Rate limiting configuration.

Defines the client key used for throttling requests (supports proxy/tests via X-Client-IP).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def client_key(request: Request) -> str:
    # Permite forçar o "IP do cliente" via header (útil em testes e atrás de proxy)
    return request.headers.get("X-Client-IP") or get_remote_address(request)


limiter = Limiter(key_func=client_key)  # Usa a chave acima pra identificar o cliente nas regras de rate limit