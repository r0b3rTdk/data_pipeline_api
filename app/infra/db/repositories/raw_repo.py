from sqlalchemy.orm import Session
from app.infra.db.models.raw_ingestion import RawIngestion

# Ordenar por id desc garante pegar o mais recente em caso de reenvio.

def find_raw_by_source_external(
    db: Session,
    source_id: int,
    external_id: str,
) -> RawIngestion | None:
    # Busca o último evento bruto por fonte + external_id
    return (
        db.query(RawIngestion)
        .filter(
            RawIngestion.source_id == source_id,
            RawIngestion.external_id == external_id,
        )
        .order_by(RawIngestion.id.desc())
        .first()
    )

def insert_raw(db: Session, raw: RawIngestion) -> RawIngestion:
    # Persiste o evento bruto no banco
    db.add(raw)
    db.commit()
    db.refresh(raw)
    return raw
