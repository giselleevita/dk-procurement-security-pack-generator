from __future__ import annotations

from dataclasses import dataclass

import requests


class GraphApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class GraphOrgInfo:
    tenant_id: str | None
    display_name: str | None


class GraphApi:
    def __init__(self, *, access_token: str):
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {access_token}"})

    def get_org(self) -> GraphOrgInfo:
        data = self._get_json("https://graph.microsoft.com/v1.0/organization?$select=id,displayName")
        items = data.get("value") or []
        first = items[0] if items else {}
        return GraphOrgInfo(tenant_id=first.get("id"), display_name=first.get("displayName"))

    def get_security_defaults(self) -> dict:
        return self._get_json("https://graph.microsoft.com/v1.0/policies/identitySecurityDefaultsEnforcementPolicy")

    def count_conditional_access_policies(self) -> int:
        data = self._get_json("https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies?$top=100&$select=id")
        items = data.get("value") or []
        return len(items)

    def count_directory_roles(self) -> int:
        data = self._get_json("https://graph.microsoft.com/v1.0/directoryRoles?$top=100&$select=id")
        items = data.get("value") or []
        return len(items)

    def _get_json(self, url: str) -> dict:
        resp = self._session.get(url, timeout=25)
        if resp.status_code in (401, 403):
            raise GraphApiError("Forbidden", status_code=resp.status_code)
        resp.raise_for_status()
        return resp.json()

