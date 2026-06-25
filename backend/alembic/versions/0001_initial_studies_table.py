"""Initial studies table (JSONB-first schema).

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "studies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("pmid", sa.String(), nullable=True),
        sa.Column("doi", sa.String(), nullable=True),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("quality_tier", sa.String(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_studies_topic", "studies", ["topic"], unique=False)
    op.create_index("idx_studies_quality_tier", "studies", ["quality_tier"], unique=False)
    op.create_index("idx_studies_score", "studies", ["score"], unique=False)
    op.create_index(
        "idx_studies_document_gin",
        "studies",
        ["document"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"document": "jsonb_path_ops"},
    )


def downgrade() -> None:
    op.drop_index("idx_studies_document_gin", table_name="studies")
    op.drop_index("idx_studies_score", table_name="studies")
    op.drop_index("idx_studies_quality_tier", table_name="studies")
    op.drop_index("idx_studies_topic", table_name="studies")
    op.drop_table("studies")
