from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from app.core.time import utcnow

import bcrypt


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw, salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def new_session_token() -> str:
    # URL-safe; stored only in cookie (raw).
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def default_session_expiry(now: datetime | None = None, *, hours: int = 24) -> datetime:
    if now is None:
        now = utcnow()
    return now + timedelta(hours=hours)

