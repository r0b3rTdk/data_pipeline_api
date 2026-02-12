"""
Audit repository.

Handles creation and querying of audit logs.
"""
from datetime import datetime

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.infra.db.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    *,
    trusted_event_id: int,
    user_id: int | None,
    action: str,
    reason: str,
    before_data: dict,
    after_data: dict,
    request_id: str | None,
) -> AuditLog:
    """
    Creates an audit log entry.

    Does not commit automatically.
    Caller is responsible for transaction control.
    """
    row = AuditLog(
        trusted_event_id=trusted_event_id,
        user_id=user_id,
        action=action,
        reason=reason,
        before_data=before_data,
        after_data=after_data,
        request_id=request_id,
    )
    db.add(row)
    db.flush()
    return row

def list_audit_logs(
    db: Session,
    *,
    trusted_event_id: int | None,
    user_id: int | None,
    date_from: datetime | None,
    date_to: datetime | None,
    page: int,
    page_size: int,
):
    """
    Returns paginated audit logs with optional filters.
    """
    
    # Base query
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    # Filtro por evento trusted
    if trusted_event_id is not None:
        stmt = stmt.where(AuditLog.trusted_event_id == trusted_event_id)
        count_stmt = count_stmt.where(AuditLog.trusted_event_id == trusted_event_id)

    # Filtro por usuário
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
        count_stmt = count_stmt.where(AuditLog.user_id == user_id)

    # Filtro por período
    if date_from is not None:
        stmt = stmt.where(AuditLog.created_at >= date_from)
        count_stmt = count_stmt.where(AuditLog.created_at >= date_from)

    if date_to is not None:
        stmt = stmt.where(AuditLog.created_at <= date_to)
        count_stmt = count_stmt.where(AuditLog.created_at <= date_to)

    # Total para paginação
    total = db.execute(count_stmt).scalar_one()
    
    # Ordenação + paginação
    stmt = (
        stmt.order_by(desc(AuditLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(stmt).scalars().all()
    return total, rows