from __future__ import annotations

from dataclasses import dataclass

import requests


class GitHubApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepoSummary:
    full_name: str
    default_branch: str
    visibility: str
    private: bool


class GitHubApi:
    def __init__(self, *, access_token: str):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def get_viewer(self) -> dict:
        return self._get_json("https://api.github.com/user")

    def list_repos(self, *, per_page: int = 100) -> list[RepoSummary]:
        data = self._get_json(f"https://api.github.com/user/repos?per_page={per_page}&sort=updated")
        out: list[RepoSummary] = []
        for r in data:
            out.append(
                RepoSummary(
                    full_name=r["full_name"],
                    default_branch=r.get("default_branch") or "main",
                    visibility=r.get("visibility") or ("private" if r.get("private") else "public"),
                    private=bool(r.get("private")),
                )
            )
        return out

    def get_branch_protection(self, *, full_name: str, branch: str) -> dict | None:
        # Returns None when branch protection is not enabled.
        url = f"https://api.github.com/repos/{full_name}/branches/{branch}/protection"
        resp = self._session.get(url, timeout=20)
        if resp.status_code == 404:
            return None
        if resp.status_code == 403:
            raise GitHubApiError(f"Forbidden: {resp.text}")
        resp.raise_for_status()
        return resp.json()

    def _get_json(self, url: str) -> dict | list:
        resp = self._session.get(url, timeout=20)
        if resp.status_code == 403:
            raise GitHubApiError(f"Forbidden: {resp.text}")
        resp.raise_for_status()
        return resp.json()

