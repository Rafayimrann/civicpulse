"""initial schema: complaints table, enums, indexes

Revision ID: 0001
Revises:
Create Date: 2026-09-26

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

category_enum = postgresql.ENUM(
    "water", "electricity", "sanitation", "roads", "streetlights", "other", name="category_enum"
)
priority_enum = postgresql.ENUM("high", "normal", "low", name="priority_enum")
status_enum = postgresql.ENUM("open", "in_progress", "resolved", "rejected", name="status_enum")


def upgrade() -> None:
    bind = op.get_bind()
    category_enum.create(bind, checkfirst=True)
    priority_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("text", sa.String(length=2000), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("reporter_contact", sa.String(length=200), nullable=True),
        sa.Column(
            "category",
            postgresql.ENUM(
                "water", "electricity", "sanitation", "roads", "streetlights", "other",
                name="category_enum", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            postgresql.ENUM("high", "normal", "low", name="priority_enum", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "open", "in_progress", "resolved", "rejected", name="status_enum", create_type=False
            ),
            nullable=False,
            server_default="open",
        ),
        sa.Column("ai_summary", sa.String(length=140), nullable=True),
        sa.Column("triaged_by", sa.String(length=50), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # DB-level length enforcement in addition to the app layer, per the brief.
        sa.CheckConstraint("char_length(text) >= 10", name="ck_complaints_text_min_length"),
        sa.CheckConstraint("char_length(location) >= 3", name="ck_complaints_location_min_length"),
    )

    # Serves GET /api/complaints filtered/sorted by status+priority (the
    # operator dashboard's default "open, high-priority first" view).
    op.create_index("ix_complaints_status_priority", "complaints", ["status", "priority"])
    # Serves GET /api/complaints default ordering (newest first) and any
    # time-windowed stats query.
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_complaints_created_at", table_name="complaints")
    op.drop_index("ix_complaints_status_priority", table_name="complaints")
    op.drop_table("complaints")

    bind = op.get_bind()
    status_enum.drop(bind, checkfirst=True)
    priority_enum.drop(bind, checkfirst=True)
    category_enum.drop(bind, checkfirst=True)
