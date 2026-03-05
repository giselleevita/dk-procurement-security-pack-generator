from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.cookies import CSRF_COOKIE_NAME, SESSION_COOKIE_NAME
from app.core.security import token_hash
from app.core.settings import get_settings, parse_allowed_origins
from app.db.session import get_db
from app.models.session import Session as DbSession
from app.models.user import User
from app.repos.sessions import get_session_by_token_hash, touch_session
from app.repos.users import get_user_by_id

# Only write last_seen_at if the previous write was older than this threshold.
# Prevents a DB write on every single authenticated request.
_TOUCH_THROTTLE_SECONDS = 300  # 5 minutes


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: DbSession


def _as_aware_utc(dt: datetime) -> datetime:
    # Postgres may return tz-aware datetimes; SQLite may return naive. Normalize to aware UTC.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_auth_ctx(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    raw = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    sess = get_session_by_token_hash(db, token_hash(raw))
    if sess is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    if sess.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    if _as_aware_utc(sess.expires_at) < _utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user = get_user_by_id(db, sess.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session user")

    # Throttle: only update last_seen_at when the previous touch is stale enough.
    # This cuts DB writes from "every request" to ~once per 5 minutes per session.
    now = _utcnow()
    last_seen = _as_aware_utc(sess.last_seen_at) if sess.last_seen_at else None
    if last_seen is None or (now - last_seen).total_seconds() > _TOUCH_THROTTLE_SECONDS:
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
    if origin is not None and origin not in set(parse_allowed_origins(settings)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin check failed")
