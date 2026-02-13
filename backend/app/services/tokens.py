from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.crypto.fernet import decrypt_str, encrypt_str
from app.models.provider_connection import ProviderConnection
from app.providers.microsoft_oauth import MicrosoftToken, refresh
from app.repos.connections import upsert_connection


def get_github_access_token(conn: ProviderConnection) -> str:
    return decrypt_str(conn.encrypted_access_token)


def get_microsoft_access_token(db: Session, conn: ProviderConnection) -> str:
    settings = get_settings()

    token = decrypt_str(conn.encrypted_access_token)
    if conn.expires_at is None:
        return token

    # Refresh a bit early to avoid race near expiry.
    if conn.expires_at > (datetime.utcnow() + timedelta(seconds=60)):
        return token

    if not conn.encrypted_refresh_token:
        return token

    refreshed: MicrosoftToken = refresh(
        tenant=settings.ms_tenant,
        client_id=settings.ms_client_id,
        client_secret=settings.ms_client_secret,
        refresh_token=decrypt_str(conn.encrypted_refresh_token),
        scope=_ms_scopes(),
    )

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

