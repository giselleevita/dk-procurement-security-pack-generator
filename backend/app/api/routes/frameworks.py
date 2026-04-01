"""GET /frameworks — returns the full NIS2 / ISO 27001 control cross-reference."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx
from app.db.session import get_db
from app.services.control_defs import CONTROLS
from app.services.framework_mappings import (
    CONTROL_FRAMEWORK_MAP,
    ISO27001_CLAUSE_LABELS,
    NIS2_ARTICLE_LABELS,
)
from app.services.gap_report import build_framework_gap_report

router = APIRouter(tags=["frameworks"])


class FrameworkRef(BaseModel):
    ref: str
    label: str


class ControlFrameworkEntry(BaseModel):
    control_key: str
    title_en: str
    nis2: list[FrameworkRef]
    iso27001: list[FrameworkRef]


class FrameworksResponse(BaseModel):
    nis2_version: str
    iso27001_version: str
    controls: list[ControlFrameworkEntry]


class GapSummary(BaseModel):
    total_controls: int
    passing_controls: int
    gap_controls: int
    unknown_controls: int


class FrameworkGapEntry(BaseModel):
    reference: str
    label: str
    total_controls: int
    passing_controls: int
    gap_controls: list[str]


class PriorityGap(BaseModel):
    control_key: str
    title_en: str
    status: str
    nis2_refs: list[str]
    iso27001_refs: list[str]


class FrameworkGapReportResponse(BaseModel):
    summary: GapSummary
    frameworks: list[FrameworkGapEntry]
    priority_gaps: list[PriorityGap]
    generated_from_control_set: list[str]


@router.get("/frameworks", response_model=FrameworksResponse)
def get_frameworks(auth: AuthContext = Depends(get_auth_ctx)) -> FrameworksResponse:
    """Return the complete NIS2 + ISO 27001:2022 control mapping."""
    entries: list[ControlFrameworkEntry] = []
    for c in CONTROLS:
        mapping = CONTROL_FRAMEWORK_MAP.get(c.key, {})
        entries.append(
            ControlFrameworkEntry(
                control_key=c.key,
                title_en=c.title_en,
                nis2=[
                    FrameworkRef(ref=r, label=NIS2_ARTICLE_LABELS.get(r, r))
                    for r in mapping.get("nis2", ())
                ],
                iso27001=[
                    FrameworkRef(ref=r, label=ISO27001_CLAUSE_LABELS.get(r, r))
                    for r in mapping.get("iso27001", ())
                ],
            )
        )
    return FrameworksResponse(
        nis2_version="NIS2 Directive (EU) 2022/2555",
        iso27001_version="ISO/IEC 27001:2022",
        controls=entries,
    )


@router.get("/frameworks/gap-report", response_model=FrameworkGapReportResponse)
def get_framework_gap_report(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
) -> FrameworkGapReportResponse:
    report = build_framework_gap_report(db, user_id=auth.user.id)
    return FrameworkGapReportResponse(**report)
