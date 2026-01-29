from sqlalchemy import BigInteger, String, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Rejection(Base):
    __tablename__ = "rejection"

    # Identificador da rejeição
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Evento bruto associado
    raw_ingestion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("raw_ingestion.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Classificação da falha
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    field: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rule: Mapped[str | None] = mapped_column(String(120), nullable=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)

    # Severidade e data
    severity: Mapped[str] = mapped_column(String(20), nullable=False, server_default="MEDIUM")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
