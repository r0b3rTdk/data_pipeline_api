"""
Security utilities.

Includes:
- API key generation and verification
- Password hashing and verification
- JWT creation and validation
"""
from alembic import op
import sqlalchemy as sa


# Identificador da migration
revision = "62924d106630"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) source_system
    # Tabela que representa os sistemas/fontes de origem

    op.create_table(
        "source_system",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("name", name="uq_source_system_name"),
        sa.CheckConstraint("status IN ('active','inactive')", name="ck_source_system_status"),
    )

    # 2) raw_ingestion
    # Tabela que guarda o evento bruto recebido

    op.create_table(
        "raw_ingestion",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.BigInteger(), sa.ForeignKey("source_system.id", ondelete="RESTRICT"), nullable=False),

        sa.Column("external_id", sa.String(120), nullable=False),
        sa.Column("schema_version", sa.String(20), nullable=False, server_default="v1"),

        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),

        sa.Column("payload_raw", sa.Text(), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),

        sa.Column("processing_status", sa.String(20), nullable=False, server_default="REJECTED"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),

        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("client_ip", sa.String(45), nullable=True),     # IPv4/IPv6
        sa.Column("user_agent", sa.String(255), nullable=True),

        sa.CheckConstraint(
            "processing_status IN ('ACCEPTED','REJECTED','DUPLICATE')",
            name="ck_raw_ingestion_processing_status",
        ),
    )

    # Índices mínimos úteis (V1)
    # Índices para busca e deduplicação

    op.create_index("ix_raw_ingestion_source_received_at", "raw_ingestion", ["source_id", "received_at"])
    op.create_index("ix_raw_ingestion_source_external_id", "raw_ingestion", ["source_id", "external_id"])
    op.create_index("ix_raw_ingestion_payload_hash", "raw_ingestion", ["payload_hash"])


def downgrade() -> None:
    op.drop_index("ix_raw_ingestion_payload_hash", table_name="raw_ingestion")
    op.drop_index("ix_raw_ingestion_source_external_id", table_name="raw_ingestion")
    op.drop_index("ix_raw_ingestion_source_received_at", table_name="raw_ingestion")

    op.drop_table("raw_ingestion")
    op.drop_table("source_system")