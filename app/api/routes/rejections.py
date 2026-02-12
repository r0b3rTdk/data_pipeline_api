"""
Rejection endpoints.

Read-only access to business rule rejections.
Restricted to analyst and admin roles.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.infra.db.repositories.rejection_repo import list_rejections
from app.api.schemas.rejection import PageResponse, RejectionItem
from app.api.deps import require_roles


# Router do módulo de rejeições
router = APIRouter(prefix="/api/v1", tags=["rejections"])


@router.get("/rejections", response_model=PageResponse)
def get_rejections(
    # Filtros opcionais
    category: str | None = Query(default=None),
    severity: str | None = Query(default=None),

    # Paginação
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),

    # Dependências
    db: Session = Depends(get_db),
    user=Depends(require_roles(["analyst", "admin"])),
):
    # Busca rejeições no repositório com paginação
    total, rows = list_rejections(
        db,
        category=category,
        severity=severity,
        page=page,
        page_size=page_size,
    )

    # Converte entidades do banco em DTOs da API
    items = [
        RejectionItem(
            id=r.id,
            raw_ingestion_id=r.raw_ingestion_id,
            category=r.category,
            field=r.field,
            rule=r.rule,
            severity=r.severity,
            message=r.message,
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