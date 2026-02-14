from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.cookies import (
    clear_csrf_cookie,
    clear_session_cookie,
    set_csrf_cookie,
    set_session_cookie,
)
from app.core.security import (
    default_session_expiry,
    hash_password,
    new_csrf_token,
    new_session_token,
    token_hash,
    verify_password,
)
from app.db.session import get_db
from app.repos.sessions import create_session, revoke_session
from app.repos.users import create_user, get_user_by_email
from app.api.deps import AuthContext, get_auth_ctx, require_csrf

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime


def _session_expiry_and_max_age() -> tuple[datetime, int]:
    now = datetime.utcnow()
    expires_at = default_session_expiry(now=now)
    max_age = max(0, int((expires_at - now).total_seconds()))
    return expires_at, max_age


def _set_login_cookies(resp: Response, *, session_token: str, csrf_token: str, max_age: int) -> None:
    # Align cookie expiry with server-side session expiry.
    set_session_cookie(resp, session_token, max_age=max_age)
    set_csrf_cookie(resp, csrf_token, max_age=max_age)


@router.post("/register", response_model=MeResponse)
def register(payload: AuthRequest, response: Response, db: Session = Depends(get_db)) -> MeResponse:
    existing = get_user_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = create_user(db, email=payload.email, password_hash=hash_password(payload.password))

    session_token = new_session_token()
    csrf_token = new_csrf_token()
    expires_at, max_age = _session_expiry_and_max_age()
    create_session(
        db,
        user_id=user.id,
        token_hash=token_hash(session_token),
        csrf_token=csrf_token,
        expires_at=expires_at,
    )
    _set_login_cookies(response, session_token=session_token, csrf_token=csrf_token, max_age=max_age)
    return MeResponse(id=str(user.id), email=user.email, created_at=user.created_at)


@router.post("/login", response_model=MeResponse)
def login(payload: AuthRequest, response: Response, db: Session = Depends(get_db)) -> MeResponse:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    session_token = new_session_token()
    csrf_token = new_csrf_token()
    expires_at, max_age = _session_expiry_and_max_age()
    create_session(
        db,
        user_id=user.id,
        token_hash=token_hash(session_token),
        csrf_token=csrf_token,
        expires_at=expires_at,
    )
    _set_login_cookies(response, session_token=session_token, csrf_token=csrf_token, max_age=max_age)
    return MeResponse(id=str(user.id), email=user.email, created_at=user.created_at)


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> dict:
    revoke_session(db, auth.session.id)
    clear_session_cookie(response)
    clear_csrf_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
def me(auth: AuthContext = Depends(get_auth_ctx)) -> MeResponse:
    u = auth.user
    return MeResponse(id=str(u.id), email=u.email, created_at=u.created_at)
