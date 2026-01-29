from sqlalchemy import BigInteger, String, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

# Aqui ficam somente eventos que passaram por validação com sucesso.

class TrustedEvent(Base):
    __tablename__ = "trusted_event"

    # Identificador do evento confiável
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Referências ao evento bruto e à fonte
    raw_ingestion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("raw_ingestion.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("source_system.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Identidade do evento
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False)

    # Tipo e status final
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_status: Mapped[str] = mapped_column(String(50), nullable=False)

    # Datas do evento
    event_timestamp: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
