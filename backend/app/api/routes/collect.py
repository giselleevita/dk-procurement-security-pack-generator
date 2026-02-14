from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.db.session import get_db
from app.services.collect import collect_now
from app.repos.audit_events import add_audit_event

router = APIRouter(tags=["collect"])


class CollectResponse(BaseModel):
    run_id: str
    status: str
    errors: list[str]


@router.post("/collect", response_model=CollectResponse)
def collect(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> CollectResponse:
    res = collect_now(db, user_id=auth.user.id)
    add_audit_event(
        db,
        user_id=auth.user.id,
        action="collect",
        metadata={"run_id": res.get("run_id"), "status": res.get("status"), "errors": res.get("errors")},
    )
    return CollectResponse(**res)

