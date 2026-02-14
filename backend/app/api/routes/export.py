from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.db.session import get_db
from app.services.export_pack import export_pack
from app.repos.audit_events import add_audit_event

router = APIRouter(tags=["export"])


@router.post("/export")
def export(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> Response:
    try:
        payload = export_pack(db, user_id=auth.user.id)
        add_audit_event(db, user_id=auth.user.id, action="export", metadata={"bytes": len(payload)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="dk-security-pack.zip"'},
    )

