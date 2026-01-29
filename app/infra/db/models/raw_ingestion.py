from sqlalchemy import BigInteger, String, DateTime, Text, Integer, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

# Essa tabela é o registro imutável de tudo que chegou no sistema.

class RawIngestion(Base):
    __tablename__ = "raw_ingestion"

    # Identificador do evento bruto
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Fonte do evento
    source_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("source_system.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Identificação externa do evento
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, server_default="v1")

    # Datas do evento e do recebimento
    event_timestamp: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    # Payload original e hash para deduplicação
    payload_raw: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Estado do processamento
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="REJECTED")
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Metadados da requisição
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
