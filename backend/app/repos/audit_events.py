from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def add_audit_event(db: Session, *, user_id: uuid.UUID, action: str, metadata: dict | None = None) -> AuditEvent:
    # Never store secrets here. Keep metadata small and deterministic.
    ev = AuditEvent(user_id=user_id, action=action, details=metadata or {}, created_at=datetime.utcnow())
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def delete_all_for_user(db: Session, *, user_id: uuid.UUID) -> None:
    db.execute(delete(AuditEvent).where(AuditEvent.user_id == user_id))
    db.commit()


def count_for_user(db: Session, *, user_id: uuid.UUID) -> int:
    stmt = select(AuditEvent).where(AuditEvent.user_id == user_id)
    return len(list(db.execute(stmt).scalars().all()))
