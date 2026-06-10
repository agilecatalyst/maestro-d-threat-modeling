"""Revision ID: 002_audit_log
Revises: 001_initial_schema
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_audit_log"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("threat_model_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["threat_model_id"], ["threat_models.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_audit_log_threat_model_id", "audit_log", ["threat_model_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_threat_model_id", table_name="audit_log")
    op.drop_table("audit_log")
