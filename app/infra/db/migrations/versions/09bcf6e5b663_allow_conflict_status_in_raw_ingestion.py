"""allow conflict status in raw_ingestion

Revision ID: 09bcf6e5b663
Revises: 9b26d99efb7d
Create Date: 2026-08-14 05:44:52.555471

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09bcf6e5b663'
down_revision: Union[str, None] = '6991eb44c131'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.drop_constraint("ck_raw_ingestion_processing_status", "raw_ingestion", type_="check")
    op.create_check_constraint(
        "ck_raw_ingestion_processing_status",
        "raw_ingestion",
        "processing_status IN ('ACCEPTED', 'REJECTED', 'DUPLICATE', 'CONFLICT')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_raw_ingestion_processing_status", "raw_ingestion", type_="check")
    op.create_check_constraint(
        "ck_raw_ingestion_processing_status",
        "raw_ingestion",
        "processing_status IN ('ACCEPTED', 'REJECTED', 'DUPLICATE')",
    )
