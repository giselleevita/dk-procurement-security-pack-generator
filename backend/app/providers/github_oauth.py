from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass(frozen=True)
class GitHubToken:
    access_token: str
    token_type: str
    scope: str
    expires_at: datetime | None = None


def exchange_code(
    *,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> GitHubToken:
    resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise ValueError(f"GitHub token exchange failed: {data.get('error_description') or data}")
    return GitHubToken(
        access_token=data["access_token"],
        token_type=data.get("token_type") or "Bearer",
        scope=data.get("scope") or "",
    )

