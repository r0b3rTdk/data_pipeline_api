from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.models.base import Base


class UserAccount(Base):
    __tablename__ = "user_account"

    # Identificador único do usuário
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # Nome de login do usuário (único)
    username: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    # Hash da senha (nunca armazenar senha em texto puro)
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Papel do usuário no sistema (RBAC)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Indica se o usuário está ativo
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    # Data de criação do usuário
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Restrições de integridade da tabela
    __table_args__ = (
        # Username não pode se repetir
        UniqueConstraint("username", name="uq_user_account_username"),

        # Apenas papéis permitidos
        CheckConstraint(
            "role IN ('admin','analyst','operator','auditor')",
            name="ck_user_account_role",
        ),
    )
