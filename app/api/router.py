"""
API router composition.

Central place where all route modules
are registered in the application.
"""

from fastapi import APIRouter

from app.api.routes import auth
from app.api.routes import trusted
from app.api.routes import rejections
from app.api.routes import health
from app.api.routes import ingest
from app.api.routes import audit
from app.api.routes import security_events
from app.api.routes import metrics


# Router principal da API
api_router = APIRouter()

# Registro dos módulos de rotas
api_router.include_router(auth.router)
api_router.include_router(trusted.router)
api_router.include_router(rejections.router)
api_router.include_router(health.router)
api_router.include_router(ingest.router)
api_router.include_router(audit.router)
api_router.include_router(security_events.router)
api_router.include_router(metrics.router)