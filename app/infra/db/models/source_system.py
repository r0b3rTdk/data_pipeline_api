from sqlalchemy import BigInteger, String, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

# Evita depender de string solta para identificar a origem.

class SourceSystem(Base):
    __tablename__ = "source_system"

    # Identificador da fonte
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Nome único do sistema de origem
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Controle de ativação da fonte
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")

    # Datas de auditoria
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
