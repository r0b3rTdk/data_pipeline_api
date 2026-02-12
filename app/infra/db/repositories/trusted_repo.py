"""
Trusted event repository.

Handles persistence and querying of validated events.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.infra.db.models.trusted_event import TrustedEvent

# Filtros são compostos dinamicamente sem quebrar a paginação.

def insert_trusted(db: Session, t: TrustedEvent) -> TrustedEvent:
    # Persiste um evento confiável
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

def list_trusted(
    db: Session,
    source_id: int | None = None,
    external_id: str | None = None,
    event_status: str | None = None,
    date_from=None,
    date_to=None,
    page: int = 1,
    page_size: int = 50,
):
    # Query base
    q = db.query(TrustedEvent)

    # Filtros opcionais
    if source_id is not None:
        q = q.filter(TrustedEvent.source_id == source_id)
    if external_id:
        q = q.filter(TrustedEvent.external_id == external_id)
    if event_status:
        q = q.filter(TrustedEvent.event_status == event_status)
    if date_from is not None:
        q = q.filter(TrustedEvent.event_timestamp >= date_from)
    if date_to is not None:
        q = q.filter(TrustedEvent.event_timestamp <= date_to)

    # Total antes da paginação
    total = q.with_entities(func.count()).scalar() or 0

    # Página atual
    items = (
        q.order_by(TrustedEvent.id.desc())
         .offset((page - 1) * page_size)
         .limit(page_size)
         .all()
    )

    return total, items

def get_trusted_by_id(db: Session, trusted_id: int) -> TrustedEvent | None:
    stmt = select(TrustedEvent).where(TrustedEvent.id == trusted_id)
    return db.execute(stmt).scalars().first()