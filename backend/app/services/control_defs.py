from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlDef:
    key: str
    provider: str  # github|microsoft|pack
    title_dk: str
    title_en: str


CONTROLS: list[ControlDef] = [
    ControlDef(
        key="ms.security_defaults",
        provider="microsoft",
        title_dk="Microsoft: Security Defaults",
        title_en="Microsoft: Security Defaults",
    ),
    ControlDef(
        key="ms.conditional_access_presence",
        provider="microsoft",
        title_dk="Microsoft: Conditional Access (tilstedeværelse)",
        title_en="Microsoft: Conditional Access (presence)",
    ),
    ControlDef(
        key="ms.admin_surface_area",
        provider="microsoft",
        title_dk="Microsoft: Admin-overflade (heuristik)",
        title_en="Microsoft: Admin surface area (heuristic)",
    ),
    ControlDef(
        key="gh.branch_protection",
        provider="github",
        title_dk="GitHub: Branch protection på default branch",
        title_en="GitHub: Branch protection on default branch",
    ),
    ControlDef(
        key="gh.pr_reviews_required",
        provider="github",
        title_dk="GitHub: PR reviews krævet",
        title_en="GitHub: PR reviews required",
    ),
    ControlDef(
        key="gh.force_pushes_disabled",
        provider="github",
        title_dk="GitHub: Force pushes deaktiveret",
        title_en="GitHub: Force pushes disabled",
    ),
    ControlDef(
        key="gh.enforce_admins",
        provider="github",
        title_dk="GitHub: Admin enforcement aktiveret",
        title_en="GitHub: Admin enforcement enabled",
    ),
    ControlDef(
        key="gh.repo_visibility_review",
        provider="github",
        title_dk="GitHub: Repo-visibility review",
        title_en="GitHub: Repo visibility review",
    ),
    ControlDef(
        key="pack.evidence_freshness",
        provider="pack",
        title_dk="Pack: Evidensens friskhed",
        title_en="Pack: Evidence freshness",
    ),
    ControlDef(
        key="pack.documentation_completeness",
        provider="pack",
        title_dk="Pack: Dokumentationsfuldstændighed",
        title_en="Pack: Documentation completeness",
    ),
    ControlDef(
        key="pack.export_integrity",
        provider="pack",
        title_dk="Pack: Eksportintegritet",
        title_en="Pack: Export integrity",
    ),
    ControlDef(
        key="pack.connection_status",
        provider="pack",
        title_dk="Pack: Forbindelsesstatus",
        title_en="Pack: Connection status",
    ),
]


CONTROL_BY_KEY = {c.key: c for c in CONTROLS}

