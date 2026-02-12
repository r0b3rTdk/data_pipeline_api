"""
AuditLog ORM model.

Stores controlled modifications made to trusted events.
Ensures full traceability of data changes.
"""
from __future__ import annotations

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    # Identificador do log
    id: Mapped[int] = mapped_column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True
    )

    # Evento trusted que sofreu alteração
    trusted_event_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("trusted_event.id", ondelete="CASCADE"), 
        nullable=False
    )
    # Usuário responsável pela alteração
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, 
        ForeignKey("user_account.id", ondelete="SET NULL"), 
        nullable=True
    )

    # Tipo da ação & # Justificativa obrigatória da alteração
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)

    # Snapshot antes/depois da modificação
    before_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    after_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # ID de rastreabilidade da requisição
    request_id: Mapped[str | None] = mapped_column(
        String(64), 
        nullable=True
    )

    # Timestamp automático da alteração
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )