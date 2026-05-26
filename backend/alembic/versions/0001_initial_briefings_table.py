"""initial briefings table

Revision ID: 0001
Revises:
Create Date: 2025-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "briefings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("condition", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("result", JSON, nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("briefings")
