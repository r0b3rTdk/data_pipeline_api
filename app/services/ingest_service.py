import json
from sqlalchemy.orm import Session

from app.api.schemas.ingest import IngestRequest
from app.core.utils import new_request_id, payload_hash
from app.domain.validation import validate_event

from app.infra.db.models.raw_ingestion import RawIngestion
from app.infra.db.models.trusted_event import TrustedEvent
from app.infra.db.models.rejection import Rejection

from app.infra.db.repositories.source_repo import create_source_if_missing
from app.infra.db.repositories.raw_repo import find_raw_by_source_external, insert_raw
from app.infra.db.repositories.trusted_repo import insert_trusted
from app.infra.db.repositories.rejection_repo import insert_rejections


def ingest_event(
    db: Session,
    req: IngestRequest,
    client_ip: str | None,
    user_agent: str | None,
):
    # Identificador único da requisição
    request_id = new_request_id()

    # Payload normalizado para hash e persistência
    payload_dict = req.model_dump(mode="json")
    raw_hash = payload_hash(payload_dict)

    # 1) Garante que a fonte exista
    src = create_source_if_missing(db, req.source)

    # 2) Deduplicação simples (source + external_id)
    existing = find_raw_by_source_external(db, src.id, req.external_id)
    if existing:
        raw = RawIngestion(
            source_id=src.id,
            external_id=req.external_id,
            schema_version=req.schema_version,
            event_timestamp=req.event_timestamp,
            payload_raw=json.dumps(payload_dict, ensure_ascii=False),
            payload_hash=raw_hash,
            processing_status="DUPLICATE",
            error_count=0,
            request_id=request_id,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        raw = insert_raw(db, raw)
        return {
            "status": "DUPLICATE",
            "raw_id": raw.id,
            "request_id": request_id,
        }

    # 3) Sempre grava o RAW primeiro
    raw = RawIngestion(
        source_id=src.id,
        external_id=req.external_id,
        schema_version=req.schema_version,
        event_timestamp=req.event_timestamp,
        payload_raw=json.dumps(payload_dict, ensure_ascii=False),
        payload_hash=raw_hash,
        processing_status="REJECTED",  # default pessimista
        error_count=0,
        request_id=request_id,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    raw = insert_raw(db, raw)

    # 4) Validação de regras de negócio
    errors = validate_event(req.event_type, req.event_status)

    if errors:
        # Converte erros em registros de rejeição
        rejs = [
            Rejection(
                raw_ingestion_id=raw.id,
                category=e["category"],
                field=e.get("field"),
                rule=e.get("rule"),
                message=e["message"],
                severity=e.get("severity", "MEDIUM"),
            )
            for e in errors
        ]
        insert_rejections(db, rejs)

        # Atualiza status do RAW
        raw.error_count = len(rejs)
        raw.processing_status = "REJECTED"
        db.commit()

        return {
            "status": "REJECTED",
            "raw_id": raw.id,
            "error_count": len(rejs),
            "request_id": request_id,
        }

    # 5) Evento validado vira TRUSTED
    trusted = TrustedEvent(
        raw_ingestion_id=raw.id,
        source_id=src.id,
        external_id=req.external_id,
        entity_id=req.entity_id,
        event_type=req.event_type,
        event_status=req.event_status,
        event_timestamp=req.event_timestamp,
    )
    trusted = insert_trusted(db, trusted)

    # Atualiza RAW como aceito
    raw.processing_status = "ACCEPTED"
    raw.error_count = 0
    db.commit()

    return {
        "status": "ACCEPTED",
        "raw_id": raw.id,
        "trusted_id": trusted.id,
        "request_id": request_id,
    }
