"""
Security events endpoints.

Read-only access to security audit events.
Restricted to auditor and admin roles.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.api.deps import require_roles
from app.api.schemas.security_events import PageResponse, SecurityEventItem
from app.infra.db.repositories.security_event_repo import list_security_events


# Router do módulo de eventos de segurança
router = APIRouter(prefix="/api/v1", tags=["security-events"])


@router.get("/security-events", response_model=PageResponse)
def get_security_events(
    # Filtros opcionais
    severity: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    source_id: int | None = Query(default=None),
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

    # Busca eventos de segurança no repositório com paginação
    total, rows = list_security_events(
        db,
        severity=severity,
        event_type=event_type,
        source_id=source_id,
        user_id=user_id,
        date_from=df,
        date_to=dt,
        page=page,
        page_size=page_size,
    )

    # Converte entidades do banco em DTOs da API
    items = [
        SecurityEventItem(
            id=r.id,
            event_type=r.event_type,
            severity=r.severity,
            source_id=r.source_id,
            user_id=r.user_id,
            ip=r.ip,
            user_agent=r.user_agent,
            request_id=r.request_id,
            details=r.details,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]

    # Resposta padronizada de paginação
    return PageResponse(
        page=page,
        page_size=page_size,
        total=total,
        items=items,
    )