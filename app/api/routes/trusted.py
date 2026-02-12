"""
Trusted events endpoints.

Read-only access to trusted events and
controlled updates with full audit logging.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.infra.db.repositories.source_repo import get_source_by_name
from app.infra.db.repositories.trusted_repo import list_trusted, get_trusted_by_id
from app.infra.db.repositories.audit_repo import create_audit_log
from app.api.schemas.trusted import PageResponse, TrustedItem, TrustedPatchRequest
from app.api.deps import require_roles


# Router do módulo de eventos confiáveis
router = APIRouter(prefix="/api/v1", tags=["trusted"])

@router.get("/trusted", response_model=PageResponse)
def get_trusted(
    # Filtros opcionais
    source: str | None = Query(default=None),
    external_id: str | None = Query(default=None),
    event_status: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),

    # Paginação
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),

    # Dependências
    db: Session = Depends(get_db),
    user=Depends(require_roles(["operator", "analyst", "admin"])),
):
    source_id = None

    # Resolve nome da fonte para source_id
    if source:
        src = get_source_by_name(db, source)
        if not src:
            # Fonte inexistente → resposta vazia
            return PageResponse(
                page=page,
                page_size=page_size,
                total=0,
                items=[],
            )
        source_id = src.id

    # Converte datas ISO para datetime
    df = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
    dt = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None

    # Busca eventos confiáveis no repositório
    total, rows = list_trusted(
        db=db,
        source_id=source_id,
        external_id=external_id,
        event_status=event_status,
        date_from=df,
        date_to=dt,
        page=page,
        page_size=page_size,
    )

    # Converte entidades do banco em DTOs da API
    items = [
        TrustedItem(
            id=r.id,
            raw_ingestion_id=r.raw_ingestion_id,
            source_id=r.source_id,
            external_id=r.external_id,
            entity_id=r.entity_id,
            event_type=r.event_type,
            event_status=r.event_status,
            event_timestamp=r.event_timestamp.isoformat(),
        )
        for r in rows
    ]

    # Resposta paginada
    return PageResponse(
        page=page,
        page_size=page_size,
        total=total,
        items=items,
    )

@router.patch("/trusted/{trusted_id}")
def patch_trusted(
    trusted_id: int,
    payload: TrustedPatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin"])),
):
    # Busca evento confiável
    row = get_trusted_by_id(db, trusted_id)
    if not row:
        raise HTTPException(status_code=404, detail="trusted_not_found")

    # Toda alteração exige justificativa
    if not payload.reason or not payload.reason.strip():
        raise HTTPException(status_code=400, detail="reason_required")

    # Snapshot antes da alteração (auditoria)
    before = {
        "event_status": row.event_status,
        "event_type": row.event_type,
        "entity_id": row.entity_id,
        "external_id": row.external_id,
    }

    # Atualiza apenas campos enviados
    if payload.event_status is not None:
        row.event_status = payload.event_status
    if payload.event_type is not None:
        row.event_type = payload.event_type

    # Snapshot após alteração
    after = {
        "event_status": row.event_status,
        "event_type": row.event_type,
        "entity_id": row.entity_id,
        "external_id": row.external_id,
    }

    # Request ID para rastreabilidade
    rid = getattr(request.state, "request_id", None)

    # Cria log de auditoria
    create_audit_log(
        db=db,
        trusted_event_id=int(row.id),
        user_id=int(user.id),
        action="UPDATE",
        reason=payload.reason.strip(),
        before_data=before,
        after_data=after,
        request_id=rid,
    )

    db.commit()

    return {"status": "updated", "id": row.id}