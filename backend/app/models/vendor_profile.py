from __future__ import annotations

import uuid
from datetime import datetime

from app.core.time import utcnow

from sqlalchemy import DateTime, Integer, String, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VendorProfile(Base):
    __tablename__ = "vendor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), unique=True, index=True, nullable=False)

    # Danish company registry
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    cvr_number: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    address: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # Contact
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    contact_email: Mapped[str] = mapped_column(String(320), nullable=False, default="")
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # Signing authority
    security_officer_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    security_officer_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    # Pack context
    pack_scope: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    pack_recipient: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    pack_validity_months: Mapped[int] = mapped_column(Integer, nullable=False, default=6)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
