from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlDef:
    key: str
    provider: str  # github|microsoft|pack
    title_dk: str
    title_en: str
    nis2_refs: tuple[str, ...] = ()
    iso27001_refs: tuple[str, ...] = ()


CONTROLS: list[ControlDef] = [
    ControlDef(
        key="ms.security_defaults",
        provider="microsoft",
        title_dk="Microsoft: Security Defaults",
        title_en="Microsoft: Security Defaults",
        nis2_refs=("art.21.2i", "art.21.2f"),
        iso27001_refs=("a.8.5", "a.5.17"),
    ),
    ControlDef(
        key="ms.conditional_access_presence",
        provider="microsoft",
        title_dk="Microsoft: Conditional Access (tilstedeværelse)",
        title_en="Microsoft: Conditional Access (presence)",
        nis2_refs=("art.21.2i", "art.21.2f"),
        iso27001_refs=("a.8.5", "a.5.15", "a.5.16"),
    ),
    ControlDef(
        key="ms.admin_surface_area",
        provider="microsoft",
        title_dk="Microsoft: Admin-overflade (heuristik)",
        title_en="Microsoft: Admin surface area (heuristic)",
        nis2_refs=("art.21.2f",),
        iso27001_refs=("a.8.2", "a.5.15"),
    ),
    ControlDef(
        key="gh.branch_protection",
        provider="github",
        title_dk="GitHub: Branch protection på default branch",
        title_en="GitHub: Branch protection on default branch",
        nis2_refs=("art.21.2e",),
        iso27001_refs=("a.8.9", "a.8.32"),
    ),
    ControlDef(
        key="gh.pr_reviews_required",
        provider="github",
        title_dk="GitHub: PR reviews krævet",
        title_en="GitHub: PR reviews required",
        nis2_refs=("art.21.2e",),
        iso27001_refs=("a.8.9", "a.8.32"),
    ),
    ControlDef(
        key="gh.force_pushes_disabled",
        provider="github",
        title_dk="GitHub: Force pushes deaktiveret",
        title_en="GitHub: Force pushes disabled",
        nis2_refs=("art.21.2e",),
        iso27001_refs=("a.8.9",),
    ),
    ControlDef(
        key="gh.enforce_admins",
        provider="github",
        title_dk="GitHub: Admin enforcement aktiveret",
        title_en="GitHub: Admin enforcement enabled",
        nis2_refs=("art.21.2f", "art.21.2e"),
        iso27001_refs=("a.8.2", "a.5.15"),
    ),
    ControlDef(
        key="gh.repo_visibility_review",
        provider="github",
        title_dk="GitHub: Repo-visibility review",
        title_en="GitHub: Repo visibility review",
        nis2_refs=("art.21.2a",),
        iso27001_refs=("a.5.1", "a.8.9"),
    ),
    ControlDef(
        key="pack.evidence_freshness",
        provider="pack",
        title_dk="Pack: Evidensens friskhed",
        title_en="Pack: Evidence freshness",
        nis2_refs=("art.21.2a", "art.23"),
        iso27001_refs=("a.8.16",),
    ),
    ControlDef(
        key="pack.documentation_completeness",
        provider="pack",
        title_dk="Pack: Dokumentationsfuldstændighed",
        title_en="Pack: Documentation completeness",
        nis2_refs=("art.21.2a",),
        iso27001_refs=("a.5.1",),
    ),
    ControlDef(
        key="pack.export_integrity",
        provider="pack",
        title_dk="Pack: Eksportintegritet",
        title_en="Pack: Export integrity",
        nis2_refs=("art.21.2g",),
        iso27001_refs=("a.8.34",),
    ),
    ControlDef(
        key="pack.connection_status",
        provider="pack",
        title_dk="Pack: Forbindelsesstatus",
        title_en="Pack: Connection status",
        nis2_refs=("art.21.2j",),
        iso27001_refs=("a.8.16",),
    ),
]


CONTROL_BY_KEY = {c.key: c for c in CONTROLS}

