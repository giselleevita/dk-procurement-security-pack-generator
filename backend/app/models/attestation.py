from __future__ import annotations

import uuid
from datetime import datetime

from app.core.time import utcnow

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Attestation(Base):
    """Manual attestation for controls that cannot be automatically collected.

    Vendors self-certify controls such as incident response, backup, encryption,
    and endpoint management. Each attestation key maps to a control in CONTROLS.
    """

    __tablename__ = "attestations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)

    # Matches a control_key in CONTROLS (e.g. "att.incident_response")
    control_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)

    # pass|warn|fail – vendor-chosen status
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")

    # Free-text self-attestation note
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Who attested (free-text name/title)
    attested_by: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    attested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
