"""
Security headers middleware.

Adds essential HTTP security headers to all responses.

Protects against:
- MIME type sniffing
- Clickjacking
- Referrer leakage
- Unnecessary browser permissions
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    # Adiciona os headers de segurança a todas as respostas
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response