"""
Audit endpoints.

Read-only access to audit logs.
Restricted to auditor and admin roles.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.api.deps import require_roles
from app.infra.db.repositories.audit_repo import list_audit_logs


# Router do módulo de auditoria
router = APIRouter(prefix="/api/v1", tags=["audit"])


@router.get("/audit")
def get_audit(
    # Filtros opcionais
    trusted_event_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),

    # Paginação
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),

    # Dependências
    db: Session = Depends(get_db),
    user=Depends(require_roles(["auditor", "admin"])),
):
    # Converte datas ISO para datetime (se fornecidas)
    df = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
    dt = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None

    # Busca logs de auditoria no repositório
    total, rows = list_audit_logs(
        db,
        trusted_event_id=trusted_event_id,
        user_id=user_id,
        date_from=df,
        date_to=dt,
        page=page,
        page_size=page_size,
    )

    # Normaliza entidades para resposta JSON
    items = [
        {
            "id": r.id,
            "trusted_event_id": r.trusted_event_id,
            "user_id": r.user_id,
            "action": r.action,
            "reason": r.reason,
            "before_data": r.before_data,
            "after_data": r.after_data,
            "request_id": r.request_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]

    # Resposta paginada
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": items,
    }