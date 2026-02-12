"""
Security event repository.

Handles creation and querying of security audit events.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

# Imports por side-effect:
# Garante que as tabelas referenciadas por ForeignKey
# estejam registradas no Base.metadata antes do uso.
from app.infra.db.models.user_account import UserAccount  # noqa: F401
from app.infra.db.models.source_system import SourceSystem  # noqa: F401

from app.infra.db.models.security_event import SecurityEvent


class SecurityEventRepository:
    """
    Repository responsible for persisting security events.
    """
    def __init__(self, db: Session) -> None:
        # Sessão do banco usada pelo repositório
        self.db = db

    def create(
        self,
        *,
        event_type: str,
        severity: str,
        source_id: Optional[int] = None,
        user_id: Optional[int] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvent:
        # Cria a entidade de evento de segurança
        ev = SecurityEvent(
            event_type=event_type,
            severity=severity,
            source_id=source_id,
            user_id=user_id,
            ip=ip,
            user_agent=user_agent,
            request_id=request_id,
            details=details or {},
        )

        # Persiste o evento no banco
        self.db.add(ev)
        self.db.commit()
        self.db.refresh(ev)

        return ev

def create_security_event(
    db: Session,
    *,
    event_type: str,
    severity: str,
    source_id: Optional[int] = None,
    user_id: Optional[int] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    details: Any = None,

    # Compatibilidade com código legado (deps.py)
    source_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    **extra: Any,
) -> SecurityEvent:
    # Mapeia actor_user_id (nome antigo) para user_id (model atual)
    if user_id is None and actor_user_id is not None:
        user_id = actor_user_id

    # Normaliza details para dict (JSONB exige isso)
    if details is None:
        details_dict: Dict[str, Any] = {}
    elif isinstance(details, dict):
        details_dict = dict(details)
    else:
        details_dict = {"message": str(details)}

    # Acrescenta metadados úteis sem sobrescrever
    if source_name is not None:
        details_dict.setdefault("source_name", source_name)
    if endpoint is not None:
        details_dict.setdefault("endpoint", endpoint)

    # Anexa qualquer informação extra enviada
    if extra:
        details_dict.update(extra)

    # Usa o repositório como ponto único de persistência
    repo = SecurityEventRepository(db)
    return repo.create(
        event_type=event_type,
        severity=severity,
        source_id=source_id,
        user_id=user_id,
        ip=ip,
        user_agent=user_agent,
        request_id=request_id,
        details=details_dict,
    )

def list_security_events(
    db: Session,
    *,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    source_id: Optional[int] = None,
    user_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
):
    stmt = select(SecurityEvent)
    count_stmt = select(func.count()).select_from(SecurityEvent)

    if severity:
        stmt = stmt.where(SecurityEvent.severity == severity)
        count_stmt = count_stmt.where(SecurityEvent.severity == severity)

    if event_type:
        stmt = stmt.where(SecurityEvent.event_type == event_type)
        count_stmt = count_stmt.where(SecurityEvent.event_type == event_type)

    if source_id is not None:
        stmt = stmt.where(SecurityEvent.source_id == source_id)
        count_stmt = count_stmt.where(SecurityEvent.source_id == source_id)

    if user_id is not None:
        stmt = stmt.where(SecurityEvent.user_id == user_id)
        count_stmt = count_stmt.where(SecurityEvent.user_id == user_id)

    if date_from is not None:
        stmt = stmt.where(SecurityEvent.created_at >= date_from)
        count_stmt = count_stmt.where(SecurityEvent.created_at >= date_from)

    if date_to is not None:
        stmt = stmt.where(SecurityEvent.created_at <= date_to)
        count_stmt = count_stmt.where(SecurityEvent.created_at <= date_to)

    total = db.execute(count_stmt).scalar_one()

    stmt = (
        stmt.order_by(desc(SecurityEvent.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(stmt).scalars().all()
    return total, rows