from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.db.session import get_db
from app.repos.connections import delete_connection, list_connections

router = APIRouter(prefix="/connections", tags=["connections"])


class ConnectionOut(BaseModel):
    provider: str
    connected: bool
    scopes: str = ""
    updated_at: datetime | None = None
    expires_at: datetime | None = None
    provider_account_id: str | None = None


@router.get("", response_model=list[ConnectionOut])
def get_connections(db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_ctx)) -> list[ConnectionOut]:
    rows = list_connections(db, user_id=auth.user.id)
    by = {r.provider: r for r in rows}
    out: list[ConnectionOut] = []
    for provider in ("github", "microsoft"):
        r = by.get(provider)
        out.append(
            ConnectionOut(
                provider=provider,
                connected=r is not None,
                scopes=r.scopes if r else "",
                updated_at=r.updated_at if r else None,
                expires_at=r.expires_at if r else None,
                provider_account_id=r.provider_account_id if r else None,
            )
        )
    return out


@router.delete("/{provider}")
def forget_provider(
    provider: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> dict:
    provider = provider.lower()
    if provider not in ("github", "microsoft"):
        return {"ok": False, "error": "unknown_provider"}
    delete_connection(db, user_id=auth.user.id, provider=provider)
    return {"ok": True}

