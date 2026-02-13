from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.db.session import get_db
from app.services.collect import collect_now

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
    return CollectResponse(**res)

