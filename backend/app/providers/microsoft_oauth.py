from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.time import utcnow

import requests


@dataclass(frozen=True)
class MicrosoftToken:
    access_token: str
    refresh_token: str | None
    token_type: str
    scope: str
    expires_at: datetime | None


def token_endpoint(tenant: str) -> str:
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


def exchange_code(
    *,
    tenant: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    scope: str,
) -> MicrosoftToken:
    resp = requests.post(
        token_endpoint(tenant),
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "scope": scope,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise ValueError(f"Microsoft token exchange failed: {data}")
    expires_at = None
    if "expires_in" in data:
        expires_at = utcnow() + timedelta(seconds=int(data["expires_in"]))
    return MicrosoftToken(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),
        token_type=data.get("token_type") or "Bearer",
        scope=data.get("scope") or scope,
        expires_at=expires_at,
    )


def refresh(
    *,
    tenant: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    scope: str,
) -> MicrosoftToken:
    resp = requests.post(
        token_endpoint(tenant),
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": scope,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise ValueError(f"Microsoft token refresh failed: {data}")
    expires_at = None
    if "expires_in" in data:
        expires_at = utcnow() + timedelta(seconds=int(data["expires_in"]))
    return MicrosoftToken(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token") or refresh_token,
        token_type=data.get("token_type") or "Bearer",
        scope=data.get("scope") or scope,
        expires_at=expires_at,
    )

