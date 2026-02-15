from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.time import utcnow

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.crypto.fernet import decrypt_str, encrypt_str
from app.models.provider_connection import ProviderConnection
from app.providers.microsoft_oauth import MicrosoftToken, refresh
from app.repos.connections import upsert_connection


class TokenError(RuntimeError):
    pass


class TokenDecryptError(TokenError):
    pass


class TokenExpiredError(TokenError):
    pass


def _as_aware_utc(dt: datetime) -> datetime:
    # DB backends may return tz-naive or tz-aware datetimes; normalize to aware UTC.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)



def get_github_access_token(conn: ProviderConnection) -> str:
    try:
        return decrypt_str(conn.encrypted_access_token)
    except ValueError as e:
        raise TokenDecryptError("GitHub token cannot be decrypted; reconnect required") from e


def get_microsoft_access_token(db: Session, conn: ProviderConnection) -> str:
    settings = get_settings()

    try:
        token = decrypt_str(conn.encrypted_access_token)
    except ValueError as e:
        raise TokenDecryptError("Microsoft token cannot be decrypted; reconnect required") from e
    if conn.expires_at is None:
        return token

    # Refresh a bit early to avoid race near expiry.
    if _as_aware_utc(conn.expires_at) > (utcnow() + timedelta(seconds=60)):
        return token

    if not conn.encrypted_refresh_token:
        raise TokenExpiredError("Microsoft token expired and no refresh token is available; reconnect required")

    try:
        refresh_token = decrypt_str(conn.encrypted_refresh_token)
    except ValueError as e:
        raise TokenDecryptError("Microsoft refresh token cannot be decrypted; reconnect required") from e

    try:
        refreshed: MicrosoftToken = refresh(
            tenant=settings.ms_tenant,
            client_id=settings.ms_client_id,
            client_secret=settings.ms_client_secret,
            refresh_token=refresh_token,
            scope=_ms_scopes(),
        )
    except Exception as e:
        raise TokenExpiredError("Microsoft token refresh failed; reconnect required") from e

    upsert_connection(
        db,
        user_id=conn.user_id,
        provider="microsoft",
        encrypted_access_token=encrypt_str(refreshed.access_token),
        encrypted_refresh_token=encrypt_str(refreshed.refresh_token) if refreshed.refresh_token else None,
        scopes=refreshed.scope,
        token_type=refreshed.token_type,
        expires_at=refreshed.expires_at,
        provider_account_id=conn.provider_account_id,
    )
    return refreshed.access_token


def _ms_scopes() -> str:
    # Keep in one place for consistency across authorize/token calls.
    return "openid profile email offline_access Organization.Read.All Policy.Read.All"
