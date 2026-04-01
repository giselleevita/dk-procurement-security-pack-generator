from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx
from app.db.session import get_db
from app.repos.evidence import latest_evidence_all_controls, latest_evidence_for_control
from app.services.control_defs import CONTROL_BY_KEY, CONTROLS

router = APIRouter(tags=["controls"])

_AGING_DAYS = 30  # alert if evidence older than this many days


class ControlSummary(BaseModel):
    key: str
    provider: str
    title_dk: str
    title_en: str
    status: str
    collected_at: datetime | None = None
    nis2_refs: list[str] = []
    iso27001_refs: list[str] = []
    age_alert: bool = False


class ControlDetail(BaseModel):
    key: str
    provider: str
    title_dk: str
    title_en: str
    status: str
    collected_at: datetime | None = None
    artifacts: dict
    notes: str
    nis2_refs: list[str] = []
    iso27001_refs: list[str] = []
    age_alert: bool = False


@router.get("/dashboard", response_model=list[ControlSummary])
def dashboard(db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_ctx)) -> list[ControlSummary]:
    latest = {r.control_key: r for r in latest_evidence_all_controls(db, user_id=auth.user.id)}
    now = datetime.now(timezone.utc)

    out: list[ControlSummary] = []
    for c in CONTROLS:
        row = latest.get(c.key)
        age_alert = False
        if row and row.collected_at:
            ts = row.collected_at if row.collected_at.tzinfo else row.collected_at.replace(tzinfo=timezone.utc)
            age_alert = (now - ts).days > _AGING_DAYS
        out.append(
            ControlSummary(
                key=c.key,
                provider=c.provider,
                title_dk=c.title_dk,
                title_en=c.title_en,
                status=row.status if row else "unknown",
                collected_at=row.collected_at if row else None,
                nis2_refs=list(c.nis2_refs),
                iso27001_refs=list(c.iso27001_refs),
                age_alert=age_alert,
            )
        )
    return out


@router.get("/controls", response_model=list[ControlSummary])
def list_controls(db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_ctx)) -> list[ControlSummary]:
    return dashboard(db=db, auth=auth)


@router.get("/controls/{control_key}", response_model=ControlDetail)
def control_detail(control_key: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_ctx)) -> ControlDetail:
    if control_key not in CONTROL_BY_KEY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown control")

    c = CONTROL_BY_KEY[control_key]
    row = latest_evidence_for_control(db, user_id=auth.user.id, control_key=control_key)
    if row is None:
        return ControlDetail(
            key=c.key,
            provider=c.provider,
            title_dk=c.title_dk,
            title_en=c.title_en,
            status="unknown",
            collected_at=None,
            artifacts={},
            notes="No evidence collected yet.",
            nis2_refs=list(c.nis2_refs),
            iso27001_refs=list(c.iso27001_refs),
        )

    now = datetime.now(timezone.utc)
    age_alert = False
    if row.collected_at:
        ts = row.collected_at if row.collected_at.tzinfo else row.collected_at.replace(tzinfo=timezone.utc)
        age_alert = (now - ts).days > _AGING_DAYS

    return ControlDetail(
        key=c.key,
        provider=c.provider,
        title_dk=c.title_dk,
        title_en=c.title_en,
        status=row.status,
        collected_at=row.collected_at,
        artifacts=row.artifacts,
        notes=row.notes,
        nis2_refs=list(c.nis2_refs),
        iso27001_refs=list(c.iso27001_refs),
        age_alert=age_alert,
    )

