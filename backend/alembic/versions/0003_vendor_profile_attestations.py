"""vendor_profile and attestations

Revision ID: 0003_vendor_profile_attestations
Revises: 0002_audit_events
Create Date: 2026-03-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0003_vendor_profile_attestations"
down_revision = "0002_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("cvr_number", sa.String(8), nullable=False, server_default=""),
        sa.Column("address", sa.String(500), nullable=False, server_default=""),
        sa.Column("contact_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("contact_email", sa.String(320), nullable=False, server_default=""),
        sa.Column("contact_phone", sa.String(50), nullable=False, server_default=""),
        sa.Column("security_officer_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("security_officer_title", sa.String(255), nullable=False, server_default=""),
        sa.Column("pack_scope", sa.String(1000), nullable=False, server_default=""),
        sa.Column("pack_recipient", sa.String(500), nullable=False, server_default=""),
        sa.Column("pack_validity_months", sa.Integer, nullable=False, server_default="6"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vendor_profiles_user_id", "vendor_profiles", ["user_id"], unique=True)

    op.create_table(
        "attestations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("control_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="unknown"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("attested_by", sa.String(255), nullable=False, server_default=""),
        sa.Column("attested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_attestations_user_id", "attestations", ["user_id"], unique=False)
    op.create_index("ix_attestations_control_key", "attestations", ["control_key"], unique=False)
    op.create_index("ix_attestations_user_control", "attestations", ["user_id", "control_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_attestations_user_control", table_name="attestations")
    op.drop_index("ix_attestations_control_key", table_name="attestations")
    op.drop_index("ix_attestations_user_id", table_name="attestations")
    op.drop_table("attestations")

    op.drop_index("ix_vendor_profiles_user_id", table_name="vendor_profiles")
    op.drop_table("vendor_profiles")
