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

        # Extra hardening
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS: só faz sentido se você estiver em HTTPS (produção/deploy)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        # CSP: mantenha conservador e sem quebrar docs/openapi
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
            response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data:; img-src 'self' data:; connect-src 'self';"
        else:
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"

        return response