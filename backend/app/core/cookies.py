from __future__ import annotations

from fastapi import Response

from app.core.settings import get_settings


SESSION_COOKIE_NAME = "dkpack_session"
CSRF_COOKIE_NAME = "dkpack_csrf"


def set_session_cookie(resp: Response, token: str) -> None:
    settings = get_settings()
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(resp: Response) -> None:
    settings = get_settings()
    resp.delete_cookie(key=SESSION_COOKIE_NAME, path="/", samesite="lax", secure=settings.cookie_secure)


def set_csrf_cookie(resp: Response, token: str) -> None:
    settings = get_settings()
    resp.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_csrf_cookie(resp: Response) -> None:
    settings = get_settings()
    resp.delete_cookie(key=CSRF_COOKIE_NAME, path="/", samesite="lax", secure=settings.cookie_secure)

