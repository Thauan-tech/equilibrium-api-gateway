"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), unique=True, nullable=False),
        sa.Column("cpf", sa.String(14), unique=True, nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("plan_type", sa.String(20), nullable=False),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("duration_days", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "member_id", UUID(as_uuid=True), sa.ForeignKey("members.id"), nullable=False
        ),
        sa.Column(
            "plan_id", UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False
        ),
        sa.Column("start_date", sa.DateTime, nullable=False),
        sa.Column("end_date", sa.DateTime, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("auto_renew", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "member_id", UUID(as_uuid=True), sa.ForeignKey("members.id"), nullable=False
        ),
        sa.Column(
            "subscription_id",
            UUID(as_uuid=True),
            sa.ForeignKey("subscriptions.id"),
            nullable=True,
        ),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("provider_transaction_id", sa.String(255), nullable=True),
        sa.Column("provider_payment_url", sa.String(500), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("paid_at", sa.DateTime, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )

    # Indexes
    op.create_index("ix_members_email", "members", ["email"])
    op.create_index("ix_members_cpf", "members", ["cpf"])
    op.create_index("ix_payments_member_id", "payments", ["member_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_subscriptions_member_id", "subscriptions", ["member_id"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("subscriptions")
    op.drop_table("plans")
    op.drop_table("members")
