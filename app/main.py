from fastapi import FastAPI

from app.api.routes.ingest import router as ingest_router
from app.api.routes.trusted import router as trusted_router
from app.api.routes.rejections import router as rejections_router
from app.api.routes.health import router as health_router

# Instância principal da aplicação FastAPI
app = FastAPI(title="Projeto01 - Data Pipeline API")

# Registro dos módulos de rotas
app.include_router(ingest_router)
app.include_router(trusted_router)
app.include_router(rejections_router)
app.include_router(health_router)
