from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.db.session import get_db
from app.repos.attestations import list_attestations, upsert_attestation
from app.services.control_defs import CONTROL_BY_KEY

router = APIRouter(tags=["attestations"])

ATTESTATION_STATUSES = {"pass", "warn", "fail", "unknown"}


class AttestationResponse(BaseModel):
    control_key: str
    status: str
    notes: str
    attested_by: str
    attested_at: datetime | None = None
    updated_at: datetime | None = None


class AttestationUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(pass|warn|fail|unknown)$")
    notes: str = Field(default="", max_length=2000)
    attested_by: str = Field(default="", max_length=255)


@router.get("/attestations", response_model=list[AttestationResponse])
def get_attestations(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
) -> list[AttestationResponse]:
    rows = list_attestations(db, user_id=auth.user.id)
    # Return one row per attestation control key (only att.* prefix)
    att_keys = {k for k in CONTROL_BY_KEY if k.startswith("att.")}
    by_key = {r.control_key: r for r in rows}
    out = []
    for key in sorted(att_keys):
        r = by_key.get(key)
        if r:
            out.append(AttestationResponse(
                control_key=r.control_key,
                status=r.status,
                notes=r.notes,
                attested_by=r.attested_by,
                attested_at=r.attested_at,
                updated_at=r.updated_at,
            ))
        else:
            out.append(AttestationResponse(
                control_key=key,
                status="unknown",
                notes="",
                attested_by="",
            ))
    return out


@router.put("/attestations/{control_key}", response_model=AttestationResponse)
def update_attestation(
    control_key: str,
    body: AttestationUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> AttestationResponse:
    if control_key not in CONTROL_BY_KEY or not control_key.startswith("att."):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown attestation control")

    att = upsert_attestation(
        db,
        user_id=auth.user.id,
        control_key=control_key,
        status=body.status,
        notes=body.notes,
        attested_by=body.attested_by,
    )
    return AttestationResponse(
        control_key=att.control_key,
        status=att.status,
        notes=att.notes,
        attested_by=att.attested_by,
        attested_at=att.attested_at,
        updated_at=att.updated_at,
    )
