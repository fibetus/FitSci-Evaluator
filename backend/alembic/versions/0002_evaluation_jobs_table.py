"""evaluation_jobs table for async evaluate workflow.

Revision ID: 0002_evaluation_jobs
Revises: 0001_initial
Create Date: 2026-06-26
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_evaluation_jobs"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("pmc_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
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
    op.create_index(
        "idx_evaluation_jobs_pmc_id_created",
        "evaluation_jobs",
        ["pmc_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_evaluation_jobs_pmc_id_created", table_name="evaluation_jobs")
    op.drop_table("evaluation_jobs")
