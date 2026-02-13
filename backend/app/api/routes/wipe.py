from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.core.cookies import clear_csrf_cookie, clear_session_cookie
from app.db.session import get_db
from app.repos.connections import delete_connection
from app.repos.evidence import delete_all_user_data
from app.repos.oauth_states import delete_all_for_user
from app.repos.sessions import delete_all_sessions_for_user

router = APIRouter(tags=["safety"])


@router.post("/wipe")
def wipe(
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> dict:
    delete_all_user_data(db, user_id=auth.user.id)
    delete_all_for_user(db, user_id=auth.user.id)
    delete_connection(db, user_id=auth.user.id, provider="github")
    delete_connection(db, user_id=auth.user.id, provider="microsoft")
    delete_all_sessions_for_user(db, user_id=auth.user.id)
    clear_session_cookie(response)
    clear_csrf_cookie(response)
    return {"ok": True}
