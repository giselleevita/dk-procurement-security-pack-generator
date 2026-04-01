"""NIS2 Directive and ISO/IEC 27001:2022 control cross-reference mappings.

Maps each ControlDef key → NIS2 articles and ISO 27001 Annex A clause references.
"""

from __future__ import annotations

# ─── NIS2 reference catalogue ──────────────────────────────────────────────────
# Format: "Art. <N> – <short title>"
NIS2_ARTICLE_LABELS: dict[str, str] = {
    "art.21": "Art. 21 – Cybersecurity risk-management measures",
    "art.21.2a": "Art. 21(2)(a) – Policies on risk analysis and security",
    "art.21.2b": "Art. 21(2)(b) – Incident handling",
    "art.21.2d": "Art. 21(2)(d) – Supply chain security",
    "art.21.2e": "Art. 21(2)(e) – Security in acquisition/development",
    "art.21.2f": "Art. 21(2)(f) – Access control and asset management",
    "art.21.2g": "Art. 21(2)(g) – Cryptography and encryption",
    "art.21.2h": "Art. 21(2)(h) – Human resources security and training",
    "art.21.2i": "Art. 21(2)(i) – Authentication (MFA/continuous)",
    "art.21.2j": "Art. 21(2)(j) – Operational security and continuity",
    "art.23": "Art. 23 – Reporting obligations",
    "art.24": "Art. 24 – Use of certified products/services",
}

# ─── ISO/IEC 27001:2022 Annex A clause labels ──────────────────────────────────
ISO27001_CLAUSE_LABELS: dict[str, str] = {
    "a.5.1": "A.5.1 – Policies for information security",
    "a.5.15": "A.5.15 – Access control",
    "a.5.16": "A.5.16 – Identity management",
    "a.5.17": "A.5.17 – Authentication information",
    "a.5.20": "A.5.20 – Addressing information security in supplier agreements",
    "a.5.23": "A.5.23 – Information security for use of cloud services",
    "a.5.32": "A.5.32 – Intellectual property rights",
    "a.6.3": "A.6.3 – Information security awareness and training",
    "a.7.2": "A.7.2 – Physical entry",
    "a.8.2": "A.8.2 – Privileged access rights",
    "a.8.5": "A.8.5 – Secure authentication",
    "a.8.6": "A.8.6 – Capacity management",
    "a.8.9": "A.8.9 – Configuration management",
    "a.8.16": "A.8.16 – Monitoring activities",
    "a.8.20": "A.8.20 – Networks security",
    "a.8.32": "A.8.32 – Change management",
    "a.8.34": "A.8.34 – Protection of information systems during audit testing",
}

# ─── Per-control mapping ────────────────────────────────────────────────────────
CONTROL_FRAMEWORK_MAP: dict[str, dict[str, tuple[str, ...]]] = {
    "ms.security_defaults": {
        "nis2": ("art.21.2i", "art.21.2f"),
        "iso27001": ("a.8.5", "a.5.17"),
    },
    "ms.conditional_access_presence": {
        "nis2": ("art.21.2i", "art.21.2f"),
        "iso27001": ("a.8.5", "a.5.15", "a.5.16"),
    },
    "ms.admin_surface_area": {
        "nis2": ("art.21.2f",),
        "iso27001": ("a.8.2", "a.5.15"),
    },
    "gh.branch_protection": {
        "nis2": ("art.21.2e",),
        "iso27001": ("a.8.9", "a.8.32"),
    },
    "gh.pr_reviews_required": {
        "nis2": ("art.21.2e",),
        "iso27001": ("a.8.9", "a.8.32"),
    },
    "gh.force_pushes_disabled": {
        "nis2": ("art.21.2e",),
        "iso27001": ("a.8.9",),
    },
    "gh.enforce_admins": {
        "nis2": ("art.21.2f", "art.21.2e"),
        "iso27001": ("a.8.2", "a.5.15"),
    },
    "gh.repo_visibility_review": {
        "nis2": ("art.21.2a",),
        "iso27001": ("a.5.1", "a.8.9"),
    },
    "pack.evidence_freshness": {
        "nis2": ("art.21.2a", "art.23"),
        "iso27001": ("a.8.16",),
    },
    "pack.documentation_completeness": {
        "nis2": ("art.21.2a",),
        "iso27001": ("a.5.1",),
    },
    "pack.export_integrity": {
        "nis2": ("art.21.2g",),
        "iso27001": ("a.8.34",),
    },
    "pack.connection_status": {
        "nis2": ("art.21.2j",),
        "iso27001": ("a.8.16",),
    },
}


def nis2_refs_for(control_key: str) -> tuple[str, ...]:
    return CONTROL_FRAMEWORK_MAP.get(control_key, {}).get("nis2", ())


def iso27001_refs_for(control_key: str) -> tuple[str, ...]:
    return CONTROL_FRAMEWORK_MAP.get(control_key, {}).get("iso27001", ())
