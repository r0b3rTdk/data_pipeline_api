"""fase4 security models

Revision ID: 0647cc47ea66
Revises: 4e1d113c69c0
Create Date: 2026-01-30 19:34:53.625927
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Identificação da migration
revision: str = "0647cc47ea66"
down_revision: Union[str, None] = "4e1d113c69c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) source_system: adiciona hash da API Key (nunca a key em texto puro)
    op.add_column(
        "source_system",
        sa.Column("api_key_hash", sa.String(128), nullable=True),
    )

    # Índice para validação rápida de API key
    op.create_index(
        "ix_source_system_api_key_hash",
        "source_system",
        ["api_key_hash"],
    )

    # 2) user_account: usuários internos do sistema (login + permissões)
    op.create_table(
        "user_account",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        # Username único
        sa.UniqueConstraint("username", name="uq_user_account_username"),

        # Controle de papéis (RBAC)
        sa.CheckConstraint(
            "role IN ('admin','analyst','operator','auditor')",
            name="ck_user_account_role",
        ),
    )

    # 3) security_event: trilha de auditoria e eventos de segurança
    op.create_table(
        "security_event",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
            server_default="MEDIUM",
        ),

        # Referência opcional à fonte (API key)
        sa.Column(
            "source_id",
            sa.BigInteger(),
            sa.ForeignKey("source_system.id", ondelete="SET NULL"),
            nullable=True,
        ),

        # Referência opcional ao usuário interno
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user_account.id", ondelete="SET NULL"),
            nullable=True,
        ),

        # Metadados da requisição
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),

        # Detalhes livres do evento (JSON)
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),

        # Data do evento
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        # Severidade controlada
        sa.CheckConstraint(
            "severity IN ('LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_security_event_severity",
        ),
    )

    # Índices para investigação e auditoria
    op.create_index("ix_security_event_created_at", "security_event", ["created_at"])
    op.create_index("ix_security_event_event_type", "security_event", ["event_type"])
    op.create_index("ix_security_event_source_id", "security_event", ["source_id"])
    op.create_index("ix_security_event_user_id", "security_event", ["user_id"])


def downgrade() -> None:
    # Remove trilha de segurança
    op.drop_index("ix_security_event_user_id", table_name="security_event")
    op.drop_index("ix_security_event_source_id", table_name="security_event")
    op.drop_index("ix_security_event_event_type", table_name="security_event")
    op.drop_index("ix_security_event_created_at", table_name="security_event")
    op.drop_table("security_event")

    # Remove usuários internos
    op.drop_table("user_account")

    # Remove API key da fonte
    op.drop_index("ix_source_system_api_key_hash", table_name="source_system")
    op.drop_column("source_system", "api_key_hash")
