from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.cookies import CSRF_COOKIE_NAME, SESSION_COOKIE_NAME
from app.core.security import token_hash
from app.core.settings import get_settings
from app.db.session import get_db
from app.models.session import Session as DbSession
from app.models.user import User
from app.repos.sessions import get_session_by_token_hash, touch_session
from app.repos.users import get_user_by_id


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: DbSession


def get_auth_ctx(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    raw = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    sess = get_session_by_token_hash(db, token_hash(raw))
    if sess is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    if sess.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    if sess.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user = get_user_by_id(db, sess.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session user")

    touch_session(db, sess.id)
    return AuthContext(user=user, session=sess)


def require_csrf(request: Request, auth: AuthContext = Depends(get_auth_ctx)) -> None:
    # Double-submit cookie: require a header equal to the CSRF cookie value.
    cookie = request.cookies.get(CSRF_COOKIE_NAME)
    header = request.headers.get("x-csrf-token")
    if not cookie or not header or cookie != header or header != auth.session.csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF check failed")

    # Bind requests to the configured web origin when present.
    settings = get_settings()
    origin = request.headers.get("origin")
    if origin is not None and origin != settings.web_base_url:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin check failed")
