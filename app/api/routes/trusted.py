from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.infra.db.repositories.source_repo import get_source_by_name
from app.infra.db.repositories.trusted_repo import list_trusted
from app.api.schemas.trusted import PageResponse, TrustedItem

# Router do módulo de eventos confiáveis
router = APIRouter(prefix="/api/v1", tags=["trusted"])

@router.get("/trusted", response_model=PageResponse)
def get_trusted(
    source: str | None = Query(default=None),        # Nome da fonte
    external_id: str | None = Query(default=None),   # ID externo
    event_status: str | None = Query(default=None),  # Status do evento
    date_from: str | None = Query(default=None),     # Filtro de data inicial
    date_to: str | None = Query(default=None),       # Filtro de data final
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    source_id = None

    # Resolve o nome da fonte para ID
    if source:
        src = get_source_by_name(db, source)
        if src:
            source_id = src.id
        else:
            # Fonte inexistente => resultado vazio
            return PageResponse(page=page, page_size=page_size, total=0, items=[])

    # Converte datas ISO para datetime
    df = datetime.fromisoformat(date_from.replace("Z", "+00:00")) if date_from else None
    dt = datetime.fromisoformat(date_to.replace("Z", "+00:00")) if date_to else None

    # Busca paginada no repositório
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

    # Mapeia entidades para DTOs
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

    return PageResponse(page=page, page_size=page_size, total=total, items=items)
