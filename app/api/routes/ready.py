"""
Readiness endpoint.

Indicates whether the API is running and the database is reachable.
Used by load balancers/orchestrators for health checks.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.infra.db.session import get_db

router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/ready")
def readiness(request: Request, db: Session = Depends(get_db)):
    checks = {"api": "ok", "db": "ok"}
    request_id = getattr(request.state, "request_id", None)

    try:
        # Sonda leve de conectividade com o banco (não depende de tabelas)
        db.execute(text("SELECT 1"))
    except Exception:
        # Se o DB falhar, sinaliza indisponibilidade para o orquestrador
        checks["db"] = "fail"
        return JSONResponse(
            status_code=503,
            content={"status": "fail", "checks": checks, "request_id": request_id},
        )

    return {
        "status": "ok",
        "checks": checks,
        "request_id": request_id,
    }