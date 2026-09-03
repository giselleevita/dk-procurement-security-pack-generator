"""store encrypted OAuth PKCE verifiers

Revision ID: 0003_oauth_pkce
Revises: 0002_audit_events
Create Date: 2026-09-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_oauth_pkce"
down_revision = "0002_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "oauth_states",
        sa.Column("encrypted_code_verifier", sa.String(length=512), nullable=True),
    )
    # OAuth states are intentionally short-lived; old non-PKCE states are invalidated.
    op.execute("DELETE FROM oauth_states")
    op.alter_column("oauth_states", "encrypted_code_verifier", nullable=False)


def downgrade() -> None:
    op.drop_column("oauth_states", "encrypted_code_verifier")
