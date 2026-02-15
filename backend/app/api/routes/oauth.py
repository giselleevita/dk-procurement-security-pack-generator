from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from app.core.time import utcnow
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.core.settings import get_settings
from app.crypto.fernet import encrypt_str
from app.db.session import get_db
from app.providers.github_oauth import exchange_code as gh_exchange
from app.providers.github_api import GitHubApi
from app.providers.microsoft_oauth import exchange_code as ms_exchange
from app.providers.graph_api import GraphApi
from app.repos.connections import upsert_connection
from app.repos.oauth_states import consume_state, create_state, delete_expired_states
from app.services.tokens import _ms_scopes

router = APIRouter(prefix="/oauth", tags=["oauth"])


class StartResponse(BaseModel):
    authorize_url: str


def _clean_err(msg: str, *, limit: int = 220) -> str:
    msg = (msg or "").replace("\n", " ").replace("\r", " ").strip()
    return msg[:limit]


def _redirect(settings, *, provider: str, status_value: str, error: str | None = None) -> RedirectResponse:
    q: dict[str, str] = {"provider": provider, "status": status_value}
    if error:
        q["error"] = _clean_err(error)
    return RedirectResponse(url=f"{settings.web_base_url}/connections?{urlencode(q)}")


@router.post("/github/start", response_model=StartResponse)
def github_start(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> StartResponse:
    settings = get_settings()
    if not settings.github_client_id or not settings.github_client_secret or not settings.github_oauth_redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub OAuth is not configured")

    delete_expired_states(db)
    state = secrets.token_urlsafe(24)
    create_state(db, user_id=auth.user.id, provider="github", state=state, expires_at=utcnow() + timedelta(minutes=10))

    scope = "repo read:org read:user"
    q = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_oauth_redirect_uri,
            "scope": scope,
            "state": state,
            "allow_signup": "false",
        }
    )
    return StartResponse(authorize_url=f"https://github.com/login/oauth/authorize?{q}")


@router.get("/github/callback")
def github_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
):
    settings = get_settings()
    if not state:
        return _redirect(settings, provider="github", status_value="error", error="Missing OAuth state")

    st = consume_state(db, user_id=auth.user.id, provider="github", state=state)
    if st is None:
        return _redirect(settings, provider="github", status_value="error", error="Invalid or expired OAuth state")

    if error:
        msg = error_description or error
        return _redirect(settings, provider="github", status_value="error", error=f"GitHub authorization failed: {msg}")

    if not code:
        return _redirect(settings, provider="github", status_value="error", error="Missing GitHub authorization code")

    try:
        tok = gh_exchange(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            code=code,
            redirect_uri=settings.github_oauth_redirect_uri,
        )
    except Exception:
        return _redirect(settings, provider="github", status_value="error", error="GitHub token exchange failed")

    provider_account_id = None
    try:
        gh = GitHubApi(access_token=tok.access_token)
        viewer = gh.get_viewer()
        provider_account_id = str(viewer.get("id")) if isinstance(viewer, dict) else None
    except Exception:
        provider_account_id = None

    upsert_connection(
        db,
        user_id=auth.user.id,
        provider="github",
        encrypted_access_token=encrypt_str(tok.access_token),
        encrypted_refresh_token=None,
        scopes=tok.scope,
        token_type=tok.token_type,
        expires_at=None,
        provider_account_id=provider_account_id,
    )

    return _redirect(settings, provider="github", status_value="connected")


@router.post("/microsoft/start", response_model=StartResponse)
def microsoft_start(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> StartResponse:
    settings = get_settings()
    if not settings.ms_client_id or not settings.ms_client_secret or not settings.ms_oauth_redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Microsoft OAuth is not configured")

    delete_expired_states(db)
    state = secrets.token_urlsafe(24)
    create_state(db, user_id=auth.user.id, provider="microsoft", state=state, expires_at=utcnow() + timedelta(minutes=10))

    q = urlencode(
        {
            "client_id": settings.ms_client_id,
            "response_type": "code",
            "redirect_uri": settings.ms_oauth_redirect_uri,
            "response_mode": "query",
            "scope": _ms_scopes(),
            "state": state,
            "prompt": "select_account",
        }
    )
    return StartResponse(authorize_url=f"https://login.microsoftonline.com/{settings.ms_tenant}/oauth2/v2.0/authorize?{q}")


@router.get("/microsoft/callback")
def microsoft_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
):
    settings = get_settings()
    if not state:
        return _redirect(settings, provider="microsoft", status_value="error", error="Missing OAuth state")

    st = consume_state(db, user_id=auth.user.id, provider="microsoft", state=state)
    if st is None:
        return _redirect(settings, provider="microsoft", status_value="error", error="Invalid or expired OAuth state")

    if error:
        msg = error_description or error
        return _redirect(settings, provider="microsoft", status_value="error", error=f"Microsoft authorization failed: {msg}")

    if not code:
        return _redirect(settings, provider="microsoft", status_value="error", error="Missing Microsoft authorization code")

    try:
        tok = ms_exchange(
            tenant=settings.ms_tenant,
            client_id=settings.ms_client_id,
            client_secret=settings.ms_client_secret,
            code=code,
            redirect_uri=settings.ms_oauth_redirect_uri,
            scope=_ms_scopes(),
        )
    except Exception:
        return _redirect(settings, provider="microsoft", status_value="error", error="Microsoft token exchange failed")

    graph = GraphApi(access_token=tok.access_token)
    try:
        org = graph.get_org()
        provider_account_id = org.tenant_id
    except Exception:
        provider_account_id = None

    upsert_connection(
        db,
        user_id=auth.user.id,
        provider="microsoft",
        encrypted_access_token=encrypt_str(tok.access_token),
        encrypted_refresh_token=encrypt_str(tok.refresh_token) if tok.refresh_token else None,
        scopes=tok.scope,
        token_type=tok.token_type,
        expires_at=tok.expires_at,
        provider_account_id=provider_account_id,
    )

    return _redirect(settings, provider="microsoft", status_value="connected")
