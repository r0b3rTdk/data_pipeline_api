from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.models.base import Base


class SecurityEvent(Base):
    __tablename__ = "security_event"

    # Identificador único do evento de segurança
    id: Mapped[int] = mapped_column(
        BigInteger, 
        primary_key=True,
        autoincrement=True
    )

    # Tipo de evento (ex: AUTH_FAILED, ACCESS_DENIED)
    event_type: Mapped[str] = mapped_column(
        String(60), 
        nullable=False
    )

    # Grau de severidade do evento
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="MEDIUM",
    )

    # Fonte externa associada (API key), se houver
    source_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("source_system.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Usuario interno associado (JWT/RBAC), se houver
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Metadados da requisição
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Informações adicionais do evento (flexivel)
    details: Mapped[dict | None] = mapped_column(
        JSONB, 
        nullable=True
    )

    # Momento em que o evento ocorreu
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
