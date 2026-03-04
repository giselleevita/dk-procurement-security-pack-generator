from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ControlDef:
    key: str
    provider: str  # github|microsoft|pack|attestation
    title_dk: str
    title_en: str
    description_dk: str = ""
    description_en: str = ""
    iso27001_clauses: tuple[str, ...] = ()
    nis2_articles: tuple[str, ...] = ()
    remediation_dk: str = ""
    remediation_en: str = ""
    # True for controls that require manual vendor self-attestation
    is_attestation: bool = False


CONTROLS: list[ControlDef] = [
    # ── Microsoft ────────────────────────────────────────────────────────────
    ControlDef(
        key="ms.security_defaults",
        provider="microsoft",
        title_dk="Microsoft: Security Defaults",
        title_en="Microsoft: Security Defaults",
        description_dk="Verificerer om Microsoft Security Defaults er aktiveret i Entra ID.",
        description_en="Verifies if Microsoft Security Defaults are enabled in Entra ID.",
        iso27001_clauses=("A.5.16", "A.5.17", "A.8.5"),
        nis2_articles=("Art. 21(2)(e)",),
        remediation_dk=(
            "Aktiver Security Defaults: Azure Portal → Entra ID → Properties → "
            "Manage Security Defaults → sæt til Enabled."
        ),
        remediation_en=(
            "Enable Security Defaults: Azure Portal → Entra ID → Properties → "
            "Manage Security Defaults → set to Enabled."
        ),
    ),
    ControlDef(
        key="ms.conditional_access_presence",
        provider="microsoft",
        title_dk="Microsoft: Conditional Access (tilstedeværelse)",
        title_en="Microsoft: Conditional Access (presence)",
        description_dk="Tæller antallet af Conditional Access-politikker konfigureret i Entra ID.",
        description_en="Counts the number of Conditional Access policies configured in Entra ID.",
        iso27001_clauses=("A.8.3", "A.8.5"),
        nis2_articles=("Art. 21(2)(e)", "Art. 21(2)(i)"),
        remediation_dk=(
            "Opret mindst én CA-politik: Azure Portal → Entra ID → Security → "
            "Conditional Access → New policy. Kræv MFA for alle brugere som minimum."
        ),
        remediation_en=(
            "Create at least one CA policy: Azure Portal → Entra ID → Security → "
            "Conditional Access → New policy. Require MFA for all users as a minimum."
        ),
    ),
    ControlDef(
        key="ms.admin_surface_area",
        provider="microsoft",
        title_dk="Microsoft: Admin-overflade (heuristik)",
        title_en="Microsoft: Admin surface area (heuristic)",
        description_dk=(
            "Heuristik baseret på antal aktive administratorroller i Entra ID. "
            "Et højt antal roller øger risikoprofilen."
        ),
        description_en=(
            "Heuristic based on the number of active admin roles in Entra ID. "
            "A high number of roles increases the risk profile."
        ),
        iso27001_clauses=("A.8.2",),
        nis2_articles=("Art. 21(2)(i)",),
        remediation_dk=(
            "Gennemgå privilegerede roller i Entra ID → Roles and administrators. "
            "Fjern unødvendige rolletildelinger og overvej Privileged Identity Management (PIM) "
            "for just-in-time adgang."
        ),
        remediation_en=(
            "Review privileged roles in Entra ID → Roles and administrators. "
            "Remove unnecessary role assignments and consider Privileged Identity Management (PIM) "
            "for just-in-time access."
        ),
    ),
    # ── GitHub ───────────────────────────────────────────────────────────────
    ControlDef(
        key="gh.branch_protection",
        provider="github",
        title_dk="GitHub: Branch protection på default branch",
        title_en="GitHub: Branch protection on default branch",
        description_dk=(
            "Kontrollerer om standardgrenen (main/master) er beskyttet "
            "på de 10 nyeste repositories i stikprøven."
        ),
        description_en=(
            "Checks if the default branch (main/master) is protected "
            "on the 10 most recent repositories in the sample."
        ),
        iso27001_clauses=("A.8.9", "A.8.32"),
        nis2_articles=("Art. 21(2)(e)", "Art. 21(2)(h)"),
        remediation_dk=(
            "Aktiver branch protection: Repository → Settings → Branches → "
            "Add branch protection rule → aktivér de ønskede regler."
        ),
        remediation_en=(
            "Enable branch protection: Repository → Settings → Branches → "
            "Add branch protection rule → enable the desired rules."
        ),
    ),
    ControlDef(
        key="gh.pr_reviews_required",
        provider="github",
        title_dk="GitHub: PR reviews krævet",
        title_en="GitHub: PR reviews required",
        description_dk="Verificerer om pull requests kræver mindst én godkendelse inden merge.",
        description_en="Verifies if pull requests require at least one approval before merging.",
        iso27001_clauses=("A.8.32",),
        nis2_articles=("Art. 21(2)(h)",),
        remediation_dk=(
            "Kræv PR-anmeldelser: Repository → Settings → Branches → "
            "Branch protection rule → Require a pull request before merging → "
            "sæt Required approving reviews til mindst 1."
        ),
        remediation_en=(
            "Require PR reviews: Repository → Settings → Branches → "
            "Branch protection rule → Require a pull request before merging → "
            "set Required approving reviews to at least 1."
        ),
    ),
    ControlDef(
        key="gh.force_pushes_disabled",
        provider="github",
        title_dk="GitHub: Force pushes deaktiveret",
        title_en="GitHub: Force pushes disabled",
        description_dk="Kontrollerer om force pushes er deaktiveret på beskyttede grene.",
        description_en="Checks if force pushes are disabled on protected branches.",
        iso27001_clauses=("A.8.32",),
        nis2_articles=("Art. 21(2)(h)",),
        remediation_dk=(
            "Deaktiver force pushes: Repository → Settings → Branches → "
            "Branch protection rule → Allow force pushes → slå fra."
        ),
        remediation_en=(
            "Disable force pushes: Repository → Settings → Branches → "
            "Branch protection rule → Allow force pushes → turn off."
        ),
    ),
    ControlDef(
        key="gh.enforce_admins",
        provider="github",
        title_dk="GitHub: Admin enforcement aktiveret",
        title_en="GitHub: Admin enforcement enabled",
        description_dk=(
            "Verificerer om branch protection-regler gælder for administratorer "
            "og ikke kun for almindelige bidragydere."
        ),
        description_en=(
            "Verifies if branch protection rules apply to administrators, "
            "not only to regular contributors."
        ),
        iso27001_clauses=("A.8.2", "A.8.32"),
        nis2_articles=("Art. 21(2)(i)",),
        remediation_dk=(
            "Aktiver admin enforcement: Repository → Settings → Branches → "
            "Branch protection rule → Include administrators."
        ),
        remediation_en=(
            "Enable admin enforcement: Repository → Settings → Branches → "
            "Branch protection rule → Include administrators."
        ),
    ),
    ControlDef(
        key="gh.repo_visibility_review",
        provider="github",
        title_dk="GitHub: Repo-visibility review",
        title_en="GitHub: Repo visibility review",
        description_dk=(
            "Identificerer offentlige repositories i stikprøven. "
            "Offentlige repositories kræver manuel vurdering."
        ),
        description_en=(
            "Identifies public repositories in the sample. "
            "Public repositories require manual review."
        ),
        iso27001_clauses=("A.5.10", "A.8.3"),
        nis2_articles=("Art. 21(2)(i)",),
        remediation_dk=(
            "Gennemgå offentlige repositories og vurder om de bør gøres private: "
            "Repository → Settings → Danger Zone → Change repository visibility."
        ),
        remediation_en=(
            "Review public repositories and assess if they should be made private: "
            "Repository → Settings → Danger Zone → Change repository visibility."
        ),
    ),
    # ── Pack hygiene ─────────────────────────────────────────────────────────
    ControlDef(
        key="pack.evidence_freshness",
        provider="pack",
        title_dk="Pack: Evidensens friskhed",
        title_en="Pack: Evidence freshness",
        description_dk="Kontrollerer om evidens er indsamlet inden for de seneste 7 dage.",
        description_en="Checks if evidence has been collected within the last 7 days.",
        iso27001_clauses=("A.5.36",),
        nis2_articles=("Art. 21(2)(h)",),
        remediation_dk="Klik 'Collect now' for at opdatere evidens inden eksport af pakken.",
        remediation_en="Click 'Collect now' to refresh evidence before exporting the pack.",
    ),
    ControlDef(
        key="pack.documentation_completeness",
        provider="pack",
        title_dk="Pack: Dokumentationsfuldstændighed",
        title_en="Pack: Documentation completeness",
        description_dk=(
            "Verificerer om alle provider-kontroller har evidensartefakter "
            "i den aktuelle indsamlingskørsel."
        ),
        description_en=(
            "Verifies if all provider controls have evidence artifacts "
            "in the current collection run."
        ),
        iso27001_clauses=("A.5.36",),
        nis2_articles=("Art. 21(4)",),
        remediation_dk="Tilslut manglende providere og kør 'Collect now'.",
        remediation_en="Connect missing providers and run 'Collect now'.",
    ),
    ControlDef(
        key="pack.export_integrity",
        provider="pack",
        title_dk="Pack: Eksportintegritet",
        title_en="Pack: Export integrity",
        description_dk="Validerer SHA-256-hash og Ed25519-signatur i eksportpakken.",
        description_en="Validates SHA-256 hashes and Ed25519 signature in the export pack.",
        iso27001_clauses=("A.5.33", "A.8.20"),
        nis2_articles=("Art. 21(2)(h)",),
        remediation_dk=(
            "Eksporter pakken på ny. Verificer integriteten via "
            "/api/exports/{export_id}/verify-endpointet."
        ),
        remediation_en=(
            "Re-export the pack. Verify integrity via "
            "the /api/exports/{export_id}/verify endpoint."
        ),
    ),
    ControlDef(
        key="pack.connection_status",
        provider="pack",
        title_dk="Pack: Forbindelsesstatus",
        title_en="Pack: Connection status",
        description_dk=(
            "Kontrollerer om begge OAuth-providere "
            "(GitHub og Microsoft) er tilsluttet og aktive."
        ),
        description_en=(
            "Checks if both OAuth providers "
            "(GitHub and Microsoft) are connected and active."
        ),
        iso27001_clauses=("A.5.36",),
        nis2_articles=(),
        remediation_dk="Tilslut begge providere via siden 'Connect'.",
        remediation_en="Connect both providers via the 'Connect' page.",
    ),
    # ── Manual attestations ───────────────────────────────────────────────────
    ControlDef(
        key="att.incident_response",
        provider="attestation",
        title_dk="Attestation: Hændelseshåndtering (IR-plan)",
        title_en="Attestation: Incident response plan",
        description_dk=(
            "Selvbekræftelse på om der eksisterer en dokumenteret IR-plan, "
            "og hvornår den sidst blev testet."
        ),
        description_en=(
            "Self-attestation on whether a documented IR plan exists "
            "and when it was last tested."
        ),
        iso27001_clauses=("A.5.26", "A.5.27"),
        nis2_articles=("Art. 21(2)(a)",),
        remediation_dk=(
            "Udarbejd en IR-plan der mindst dækker: roller og ansvar, "
            "kommunikation, eskalering, og genopretning. Test planen mindst én gang om året."
        ),
        remediation_en=(
            "Create an IR plan covering at minimum: roles and responsibilities, "
            "communication, escalation, and recovery. Test the plan at least once per year."
        ),
        is_attestation=True,
    ),
    ControlDef(
        key="att.backup_and_recovery",
        provider="attestation",
        title_dk="Attestation: Backup og genopretning",
        title_en="Attestation: Backup and recovery",
        description_dk=(
            "Selvbekræftelse på at der gennemføres regelmæssig backup, "
            "og at restore er testet."
        ),
        description_en=(
            "Self-attestation that regular backups are performed "
            "and that restoration has been tested."
        ),
        iso27001_clauses=("A.8.13",),
        nis2_articles=("Art. 21(2)(c)",),
        remediation_dk=(
            "Konfigurér automatisk backup med defineret RPO/RTO. "
            "Test restore mindst én gang om kvartalet og dokumentér resultatet."
        ),
        remediation_en=(
            "Configure automated backup with defined RPO/RTO. "
            "Test restoration at least quarterly and document the result."
        ),
        is_attestation=True,
    ),
    ControlDef(
        key="att.encryption_at_rest_in_transit",
        provider="attestation",
        title_dk="Attestation: Kryptering (data i ro og under transport)",
        title_en="Attestation: Encryption (data at rest and in transit)",
        description_dk=(
            "Selvbekræftelse på at data krypteres i ro (AES-256 eller tilsvarende) "
            "og under transport (TLS 1.2+)."
        ),
        description_en=(
            "Self-attestation that data is encrypted at rest (AES-256 or equivalent) "
            "and in transit (TLS 1.2+)."
        ),
        iso27001_clauses=("A.8.24",),
        nis2_articles=("Art. 21(2)(g)",),
        remediation_dk=(
            "Aktivér kryptering i databasen og på diskvolumener. "
            "Brug TLS 1.2 eller 1.3 for al netværkskommunikation. "
            "Dokumentér nøglehåndteringsprocedurer."
        ),
        remediation_en=(
            "Enable encryption on the database and disk volumes. "
            "Use TLS 1.2 or 1.3 for all network communication. "
            "Document key management procedures."
        ),
        is_attestation=True,
    ),
    ControlDef(
        key="att.endpoint_management",
        provider="attestation",
        title_dk="Attestation: Endpoint-styring (MDM/EDR)",
        title_en="Attestation: Endpoint management (MDM/EDR)",
        description_dk=(
            "Selvbekræftelse på at endpoints (bærbare/stationære) "
            "administreres via MDM/EMM og at EDR/antivirus er installeret."
        ),
        description_en=(
            "Self-attestation that endpoints (laptops/desktops) "
            "are managed via MDM/EMM and that EDR/antivirus is installed."
        ),
        iso27001_clauses=("A.8.7", "A.8.9"),
        nis2_articles=("Art. 21(2)(i)",),
        remediation_dk=(
            "Implementér MDM-løsning (f.eks. Microsoft Intune, Jamf) "
            "og EDR-produkt på alle endpoints. Håndhæv diskkryptering og screenlås."
        ),
        remediation_en=(
            "Implement an MDM solution (e.g., Microsoft Intune, Jamf) "
            "and EDR product on all endpoints. Enforce disk encryption and screen lock."
        ),
        is_attestation=True,
    ),
    ControlDef(
        key="att.vulnerability_management",
        provider="attestation",
        title_dk="Attestation: Sårbarhedsstyring",
        title_en="Attestation: Vulnerability management",
        description_dk=(
            "Selvbekræftelse på at der gennemføres regelmæssig sårbarhedsscanning "
            "og at kritiske CVE'er patches inden for defineret tidsramme."
        ),
        description_en=(
            "Self-attestation that regular vulnerability scanning is performed "
            "and critical CVEs are patched within a defined timeframe."
        ),
        iso27001_clauses=("A.8.8",),
        nis2_articles=("Art. 21(2)(e)",),
        remediation_dk=(
            "Kør sårbarhedsscanning ugentligt (f.eks. Dependabot, Snyk, Trivy). "
            "Definer SLA for patching: kritisk ≤7 dage, høj ≤30 dage."
        ),
        remediation_en=(
            "Run vulnerability scanning weekly (e.g., Dependabot, Snyk, Trivy). "
            "Define patching SLA: critical ≤7 days, high ≤30 days."
        ),
        is_attestation=True,
    ),
    ControlDef(
        key="att.gdpr_dpa",
        provider="attestation",
        title_dk="Attestation: GDPR – Databehandleraftale (DPA)",
        title_en="Attestation: GDPR – Data Processing Agreement (DPA)",
        description_dk=(
            "Selvbekræftelse på at virksomheden kan tilbyde en GDPR-kompatibel "
            "databehandleraftale til kunder, der sender personoplysninger."
        ),
        description_en=(
            "Self-attestation that the company can provide a GDPR-compliant "
            "Data Processing Agreement to customers sending personal data."
        ),
        iso27001_clauses=("A.5.31", "A.5.34"),
        nis2_articles=("Art. 21(2)(d)",),
        remediation_dk=(
            "Udarbejd en DPA i overensstemmelse med GDPR Art. 28. "
            "Vedlæg liste over underdatabehandlere og overførselsgrundlag. "
            "Datatilsynets vejledning: datatilsynet.dk."
        ),
        remediation_en=(
            "Draft a DPA compliant with GDPR Art. 28. "
            "Include a list of sub-processors and transfer mechanisms. "
            "Danish DPA guidance: datatilsynet.dk."
        ),
        is_attestation=True,
    ),
]


CONTROL_BY_KEY = {c.key: c for c in CONTROLS}
