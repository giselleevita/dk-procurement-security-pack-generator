from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.vendor_profile import VendorProfile


def get_vendor_profile(db: Session, *, user_id: uuid.UUID) -> VendorProfile | None:
    stmt = select(VendorProfile).where(VendorProfile.user_id == user_id)
    return db.execute(stmt).scalars().first()


def upsert_vendor_profile(db: Session, *, user_id: uuid.UUID, data: dict) -> VendorProfile:
    vp = get_vendor_profile(db, user_id=user_id)
    now = utcnow()
    if vp is None:
        vp = VendorProfile(user_id=user_id, created_at=now, updated_at=now)
        db.add(vp)

    allowed = {
        "company_name",
        "cvr_number",
        "address",
        "contact_name",
        "contact_email",
        "contact_phone",
        "security_officer_name",
        "security_officer_title",
        "pack_scope",
        "pack_recipient",
        "pack_validity_months",
    }
    for k, v in data.items():
        if k in allowed:
            setattr(vp, k, v)
    vp.updated_at = now
    db.commit()
    db.refresh(vp)
    return vp


def delete_vendor_profile(db: Session, *, user_id: uuid.UUID) -> None:
    vp = get_vendor_profile(db, user_id=user_id)
    if vp is not None:
        db.delete(vp)
        db.commit()
