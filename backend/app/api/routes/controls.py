from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx
from app.db.session import get_db
from app.repos.evidence import latest_evidence_all_controls, latest_evidence_for_control
from app.services.control_defs import CONTROL_BY_KEY, CONTROLS

router = APIRouter(tags=["controls"])


class ControlSummary(BaseModel):
    key: str
    provider: str
    title_dk: str
    title_en: str
    description_dk: str
    description_en: str
    is_attestation: bool
    status: str
    collected_at: datetime | None = None


class ControlDetail(BaseModel):
    key: str
    provider: str
    title_dk: str
    title_en: str
    description_dk: str
    description_en: str
    iso27001_clauses: list[str]
    nis2_articles: list[str]
    remediation_dk: str
    remediation_en: str
    is_attestation: bool
    status: str
    collected_at: datetime | None = None
    artifacts: dict
    notes: str


def _summary(c, row) -> ControlSummary:
    return ControlSummary(
        key=c.key,
        provider=c.provider,
        title_dk=c.title_dk,
        title_en=c.title_en,
        description_dk=c.description_dk,
        description_en=c.description_en,
        is_attestation=c.is_attestation,
        status=row.status if row else "unknown",
        collected_at=row.collected_at if row else None,
    )


@router.get("/dashboard", response_model=list[ControlSummary])
def dashboard(db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_ctx)) -> list[ControlSummary]:
    latest = {r.control_key: r for r in latest_evidence_all_controls(db, user_id=auth.user.id)}
    return [_summary(c, latest.get(c.key)) for c in CONTROLS]


@router.get("/controls", response_model=list[ControlSummary])
def list_controls(db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_ctx)) -> list[ControlSummary]:
    return dashboard(db=db, auth=auth)


@router.get("/controls/{control_key}", response_model=ControlDetail)
def control_detail(control_key: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_ctx)) -> ControlDetail:
    if control_key not in CONTROL_BY_KEY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown control")

    c = CONTROL_BY_KEY[control_key]
    row = latest_evidence_for_control(db, user_id=auth.user.id, control_key=control_key)

    base = dict(
        key=c.key,
        provider=c.provider,
        title_dk=c.title_dk,
        title_en=c.title_en,
        description_dk=c.description_dk,
        description_en=c.description_en,
        iso27001_clauses=list(c.iso27001_clauses),
        nis2_articles=list(c.nis2_articles),
        remediation_dk=c.remediation_dk,
        remediation_en=c.remediation_en,
        is_attestation=c.is_attestation,
    )

    if row is None:
        return ControlDetail(**base, status="unknown", collected_at=None, artifacts={}, notes="No evidence collected yet.")

    return ControlDetail(**base, status=row.status, collected_at=row.collected_at, artifacts=row.artifacts, notes=row.notes)
