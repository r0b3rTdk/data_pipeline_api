from alembic import op
import sqlalchemy as sa

revision = "4e1d113c69c0"
down_revision = "62924d106630"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Eventos que passaram por validação e são confiáveis
    op.create_table(
        "trusted_event",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("raw_ingestion_id", sa.BigInteger(), sa.ForeignKey("raw_ingestion.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_id", sa.BigInteger(), sa.ForeignKey("source_system.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("external_id", sa.String(120), nullable=False),
        sa.Column("entity_id", sa.String(120), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_status", sa.String(50), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("raw_ingestion_id", name="uq_trusted_event_raw_ingestion_id"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_trusted_event_source_external"),
    )

    # Índices voltados para leitura e filtros comuns
    op.create_index("ix_trusted_event_source_event_timestamp", "trusted_event", ["source_id", "event_timestamp"])
    op.create_index("ix_trusted_event_entity_event_timestamp", "trusted_event", ["entity_id", "event_timestamp"])
    op.create_index("ix_trusted_event_event_status", "trusted_event", ["event_status"])

    # Rejeições geradas durante o processamento
    op.create_table(
        "rejection",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("raw_ingestion_id", sa.BigInteger(), sa.ForeignKey("raw_ingestion.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("field", sa.String(120), nullable=True),
        sa.Column("rule", sa.String(120), nullable=True),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_rejection_severity"),
    )

    # Índices para análise e filtros
    op.create_index("ix_rejection_raw_ingestion_id", "rejection", ["raw_ingestion_id"])
    op.create_index("ix_rejection_category_created_at", "rejection", ["category", "created_at"])
    op.create_index("ix_rejection_severity_created_at", "rejection", ["severity", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_rejection_severity_created_at", table_name="rejection")
    op.drop_index("ix_rejection_category_created_at", table_name="rejection")
    op.drop_index("ix_rejection_raw_ingestion_id", table_name="rejection")
    op.drop_table("rejection")

    op.drop_index("ix_trusted_event_event_status", table_name="trusted_event")
    op.drop_index("ix_trusted_event_entity_event_timestamp", table_name="trusted_event")
    op.drop_index("ix_trusted_event_source_event_timestamp", table_name="trusted_event")
    op.drop_table("trusted_event")
