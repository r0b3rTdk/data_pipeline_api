"""
Metrics endpoints.

Provides aggregated system metrics for analysis.
Restricted to operator, analyst and admin roles.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.api.deps import require_roles
from app.api.schemas.metrics import MetricsResponse
from app.infra.db.repositories.metrics_repo import get_metrics


router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
def metrics(
    # Filtros opcionais
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    source_id: int | None = Query(default=None),

    # Configuração de ranking
    top_n: int = Query(default=5, ge=1, le=20),

    # Dependências
    db: Session = Depends(get_db),
    user=Depends(require_roles(["operator", "analyst", "admin"])),
):
    # Converte datas ISO para datetime
    df = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
    dt = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None

    # Obtém métricas agregadas do repositório
    data = get_metrics(
        db,
        date_from=df,
        date_to=dt,
        source_id=source_id,
        top_n=top_n,
    )

    return data