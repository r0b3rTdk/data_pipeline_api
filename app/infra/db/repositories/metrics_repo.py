"""
Metrics repository.

Provides aggregated statistics about the ingestion pipeline.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infra.db.models.raw_ingestion import RawIngestion
from app.infra.db.models.trusted_event import TrustedEvent
from app.infra.db.models.rejection import Rejection


def _apply_date_filter(q, model, date_from: Optional[datetime], date_to: Optional[datetime]):
    """
    Applies date filter dynamically if the model has a created_at column.
    Keeps compatibility across different tables.
    """
    col = getattr(model, "created_at", None)
    if col is None:
        return q
    if date_from is not None:
        q = q.filter(col >= date_from)
    if date_to is not None:
        q = q.filter(col <= date_to)
    return q


def get_metrics(
    db: Session,
    *,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    source_id: Optional[int] = None,
    top_n: int = 5,
) -> Dict[str, Any]:
    
    # === RAW COUNT ===
    q_raw = db.query(func.count()).select_from(RawIngestion)
    q_raw = _apply_date_filter(q_raw, RawIngestion, date_from, date_to)
    if source_id is not None and getattr(RawIngestion, "source_id", None) is not None:
        q_raw = q_raw.filter(RawIngestion.source_id == source_id)
    total_raw = int(q_raw.scalar() or 0)

    # === TRUSTED COUNT ===
    q_trusted = db.query(func.count()).select_from(TrustedEvent)
    q_trusted = _apply_date_filter(q_trusted, TrustedEvent, date_from, date_to)
    if source_id is not None:
        q_trusted = q_trusted.filter(TrustedEvent.source_id == source_id)
    total_trusted = int(q_trusted.scalar() or 0)

    # === REJEICTIONS COUNT ===
    q_rej = db.query(func.count()).select_from(Rejection)
    q_rej = _apply_date_filter(q_rej, Rejection, date_from, date_to)
    total_rejected = int(q_rej.scalar() or 0)

    # === DUPLICATES COUNT ===
    duplicates = 0
    if getattr(RawIngestion, "processing_status", None) is not None:
        q_dup = db.query(func.count()).select_from(RawIngestion)
        q_dup = _apply_date_filter(q_dup, RawIngestion, date_from, date_to)
        if source_id is not None and getattr(RawIngestion, "source_id", None) is not None:
            q_dup = q_dup.filter(RawIngestion.source_id == source_id)
        q_dup = q_dup.filter(RawIngestion.processing_status == "DUPLICATE")
        duplicates = int(q_dup.scalar() or 0)

    # === Principais Categorias de Rejeição ===
    q_cat = db.query(Rejection.category, func.count().label("count")).select_from(Rejection)
    q_cat = _apply_date_filter(q_cat, Rejection, date_from, date_to)
    q_cat = q_cat.group_by(Rejection.category).order_by(func.count().desc()).limit(top_n)
    top_categories: List[Dict[str, Any]] = [{"category": c, "count": int(n)} for (c, n) in q_cat.all()]


    # === REJECTION RATE ===
    rejection_rate = float(total_rejected / total_raw) if total_raw > 0 else 0.0

    return {
        "total_raw": total_raw,
        "total_trusted": total_trusted,
        "total_rejected": total_rejected,
        "rejection_rate": rejection_rate,
        "duplicates": duplicates,
        "top_rejection_categories": top_categories,
    }