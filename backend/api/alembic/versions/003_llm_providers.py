"""Revision ID: 003_llm_providers
Revises: 002_audit_log
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_llm_providers"
down_revision = "002_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_provider_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("model", sa.String(length=256), nullable=False),
        sa.Column("api_key_env", sa.String(length=128), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("timeout_sec", sa.Integer(), nullable=False, server_default=sa.text("180")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("name", name="uq_llm_provider_profiles_name"),
    )
    op.create_table(
        "llm_role_bindings",
        sa.Column("role", sa.String(length=32), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["llm_provider_profiles.id"], ondelete="RESTRICT"),
    )


def downgrade() -> None:
    op.drop_table("llm_role_bindings")
    op.drop_table("llm_provider_profiles")
