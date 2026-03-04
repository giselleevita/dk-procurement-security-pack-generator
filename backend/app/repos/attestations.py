from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.attestation import Attestation


def list_attestations(db: Session, *, user_id: uuid.UUID) -> list[Attestation]:
    stmt = select(Attestation).where(Attestation.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


def get_attestation(db: Session, *, user_id: uuid.UUID, control_key: str) -> Attestation | None:
    stmt = select(Attestation).where(Attestation.user_id == user_id, Attestation.control_key == control_key)
    return db.execute(stmt).scalars().first()


def upsert_attestation(
    db: Session,
    *,
    user_id: uuid.UUID,
    control_key: str,
    status: str,
    notes: str,
    attested_by: str,
    attested_at: datetime | None = None,
) -> Attestation:
    att = get_attestation(db, user_id=user_id, control_key=control_key)
    now = utcnow()
    stamp = attested_at or now
    if att is None:
        att = Attestation(user_id=user_id, control_key=control_key, attested_at=stamp, updated_at=now)
        db.add(att)

    att.status = status
    att.notes = notes
    att.attested_by = attested_by
    att.attested_at = stamp
    att.updated_at = now
    db.commit()
    db.refresh(att)
    return att


def delete_all_for_user(db: Session, *, user_id: uuid.UUID) -> None:
    db.execute(delete(Attestation).where(Attestation.user_id == user_id))
    db.commit()
