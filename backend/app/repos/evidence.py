from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.models.evidence import ControlEvidence, EvidenceRun


def create_run(db: Session, *, user_id: uuid.UUID) -> EvidenceRun:
    run = EvidenceRun(user_id=user_id, started_at=datetime.utcnow(), status="success")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def latest_run(db: Session, *, user_id: uuid.UUID) -> EvidenceRun | None:
    stmt = select(EvidenceRun).where(EvidenceRun.user_id == user_id).order_by(desc(EvidenceRun.started_at)).limit(1)
    return db.execute(stmt).scalars().first()


def finish_run(db: Session, *, run_id: uuid.UUID, status: str, error_summary: str | None) -> None:
    run = db.get(EvidenceRun, run_id)
    if run is None:
        return
    run.finished_at = datetime.utcnow()
    run.status = status
    run.error_summary = error_summary
    db.add(run)
    db.commit()


def add_control_evidence(
    db: Session,
    *,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
    control_key: str,
    provider: str | None,
    status: str,
    artifacts: dict,
    notes: str,
    collected_at: datetime | None = None,
) -> ControlEvidence:
    row = ControlEvidence(
        user_id=user_id,
        run_id=run_id,
        control_key=control_key,
        provider=provider,
        status=status,
        artifacts=artifacts,
        notes=notes,
        collected_at=collected_at or datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def latest_evidence_for_control(db: Session, *, user_id: uuid.UUID, control_key: str) -> ControlEvidence | None:
    stmt = (
        select(ControlEvidence)
        .where(ControlEvidence.user_id == user_id, ControlEvidence.control_key == control_key)
        .order_by(desc(ControlEvidence.collected_at))
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def latest_evidence_all_controls(db: Session, *, user_id: uuid.UUID) -> list[ControlEvidence]:
    # MVP-friendly: fetch all rows and reduce in Python (12 controls max).
    stmt = select(ControlEvidence).where(ControlEvidence.user_id == user_id).order_by(desc(ControlEvidence.collected_at))
    rows = list(db.execute(stmt).scalars().all())
    seen: set[str] = set()
    out: list[ControlEvidence] = []
    for r in rows:
        if r.control_key in seen:
            continue
        seen.add(r.control_key)
        out.append(r)
    return out


def delete_all_user_data(db: Session, *, user_id: uuid.UUID) -> None:
    db.execute(delete(ControlEvidence).where(ControlEvidence.user_id == user_id))
    db.execute(delete(EvidenceRun).where(EvidenceRun.user_id == user_id))
    db.commit()
