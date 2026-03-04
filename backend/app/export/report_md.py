from __future__ import annotations

from datetime import datetime

from app.services.control_defs import CONTROLS


def render_report_md(
    *,
    generated_at: datetime,
    app_version: str,
    evidence_by_key: dict[str, dict],
    vendor: dict | None = None,
) -> str:
    vendor = vendor or {}

    company = vendor.get("company_name") or ""
    cvr = vendor.get("cvr_number") or ""
    address = vendor.get("address") or ""
    contact_name = vendor.get("contact_name") or ""
    contact_email = vendor.get("contact_email") or ""
    contact_phone = vendor.get("contact_phone") or ""
    officer_name = vendor.get("security_officer_name") or ""
    officer_title = vendor.get("security_officer_title") or ""
    scope = vendor.get("pack_scope") or ""
    recipient = vendor.get("pack_recipient") or ""
    validity_months = vendor.get("pack_validity_months") or 6

    lines: list[str] = []
    lines.append("# DK Procurement Security Pack\n\n")
    lines.append(f"Generated (UTC): {generated_at.isoformat()}Z\n")
    lines.append(f"App version: {app_version}\n\n")

    # Vendor identity block
    if any([company, cvr, scope, recipient]):
        lines.append("## Vendor / Udsteder\n\n")
        if company:
            lines.append(f"**Virksomhed / Company:** {company}  \n")
        if cvr:
            lines.append(f"**CVR-nummer / CVR number:** {cvr}  \n")
        if address:
            lines.append(f"**Adresse / Address:** {address}  \n")
        contact_parts = [x for x in [contact_name, contact_email, contact_phone] if x]
        if contact_parts:
            lines.append(f"**Kontakt / Contact:** {', '.join(contact_parts)}  \n")
        sig_parts = [x for x in [officer_name, officer_title] if x]
        if sig_parts:
            lines.append(f"**Sikkerhedsansvarlig / Security Officer:** {', '.join(sig_parts)}  \n")
        if scope:
            lines.append(f"**Leveranceomfang / Pack scope:** {scope}  \n")
        if recipient:
            lines.append(f"**Modtager / Recipient:** {recipient}  \n")
        lines.append(f"**Gyldig i / Valid for:** {validity_months} måneder / months  \n\n")

    lines.append("## Data handling statement (EN)\n")
    lines.append("- This pack is generated locally in your environment (self-hosted).\n")
    lines.append("- No telemetry and no external analytics.\n")
    lines.append("- OAuth tokens are stored encrypted in the database (Fernet).\n")
    lines.append('- Evidence is fetched only when you manually click "Collect now".\n')
    lines.append("- Export packs do not include tokens, client secrets, or encryption keys.\n")
    lines.append('- Data can be deleted via "Forget provider" and "Wipe all data".\n\n')

    lines.append("## Databehandling (DK)\n")
    lines.append("- Denne pakke er genereret lokalt i jeres miljø (self-hosted).\n")
    lines.append("- Ingen telemetry og ingen ekstern analytics.\n")
    lines.append("- OAuth tokens lagres krypteret i databasen (Fernet).\n")
    lines.append('- Evidens hentes kun ved manuel "Collect now".\n')
    lines.append("- Eksportpakker indeholder ikke tokens, client secrets eller nøgler.\n")
    lines.append('- Data kan slettes via "Forget provider" og "Wipe all data".\n\n')

    # Evidence summary
    status_counts = {"pass": 0, "warn": 0, "fail": 0, "unknown": 0}
    by_provider: dict[str, dict[str, int]] = {}
    unknown_controls: list[tuple[str, str]] = []

    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        status = (ev.get("status") or "unknown").lower()
        status_counts[status] = status_counts.get(status, 0) + 1

        by_provider.setdefault(c.provider, {"pass": 0, "warn": 0, "fail": 0, "unknown": 0})
        by_provider[c.provider][status] = by_provider[c.provider].get(status, 0) + 1

        if status == "unknown":
            notes = (ev.get("notes") or "").strip()
            unknown_controls.append((c.key, notes))

    lines.append("## Evidence Summary\n\n")
    lines.append(f"- Controls total: {len(CONTROLS)}\n")
    lines.append(f"- Pass: {status_counts.get('pass', 0)}\n")
    lines.append(f"- Warn: {status_counts.get('warn', 0)}\n")
    lines.append(f"- Fail: {status_counts.get('fail', 0)}\n")
    lines.append(f"- Unknown: {status_counts.get('unknown', 0)}\n\n")

    lines.append("### By provider\n\n")
    lines.append("| Provider | Pass | Warn | Fail | Unknown |\n")
    lines.append("|---|---:|---:|---:|---:|\n")
    for provider in ("microsoft", "github", "pack", "attestation"):
        p = by_provider.get(provider, {"pass": 0, "warn": 0, "fail": 0, "unknown": 0})
        if any(v > 0 for v in p.values()):
            lines.append(f"| {provider} | {p['pass']} | {p['warn']} | {p['fail']} | {p['unknown']} |\n")
    lines.append("\n")

    if unknown_controls:
        lines.append("### Unknown controls\n\n")
        for key, notes in unknown_controls:
            if notes:
                lines.append(f"- `{key}`: {notes}\n")
            else:
                lines.append(f"- `{key}`\n")
        lines.append("\n")

    # Compliance framework mapping table
    lines.append("## Compliance Framework Mapping\n\n")
    lines.append("| Control | Status | ISO 27001:2022 | NIS2 |\n")
    lines.append("|---|:---:|---|---|\n")
    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        status = ev.get("status") or "unknown"
        iso = ", ".join(c.iso27001_clauses) if c.iso27001_clauses else "—"
        nis2 = ", ".join(c.nis2_articles) if c.nis2_articles else "—"
        lines.append(f"| {c.title_en} | **{status}** | {iso} | {nis2} |\n")
    lines.append("\n")

    # GitHub per-repo summary table (derived from existing artifacts).
    gh = evidence_by_key.get("gh.branch_protection") or {}
    gh_art = (gh.get("artifacts") or {}) if isinstance(gh.get("artifacts"), dict) else {}
    per_repo = gh_art.get("per_repo") if isinstance(gh_art, dict) else None
    if isinstance(per_repo, list) and per_repo:
        lines.append("## GitHub repo sample summary\n\n")
        lines.append("| Repo | Protected | PR reviews | Force pushes allowed | Enforce admins | Visibility | Error |\n")
        lines.append("|---|---:|---:|---:|---:|---|---|\n")
        for r in per_repo:
            if not isinstance(r, dict):
                continue
            lines.append(
                "| {repo} | {protected} | {pr} | {fp} | {admins} | {vis} | {err} |\n".format(
                    repo=r.get("repo", ""),
                    protected="yes" if r.get("protected") else "no",
                    pr="yes" if r.get("pr_reviews_required") else "no",
                    fp="yes" if r.get("force_pushes_allowed") else "no",
                    admins="yes" if r.get("enforce_admins") else "no",
                    vis=r.get("visibility") or "",
                    err=(r.get("error") or "").replace("\n", " ")[:120],
                )
            )
        lines.append("\n")

    # Automated controls
    automated = [c for c in CONTROLS if not c.is_attestation]
    attestation_controls = [c for c in CONTROLS if c.is_attestation]

    lines.append("## Controls\n\n")
    for c in automated:
        ev = evidence_by_key.get(c.key) or {}
        status = ev.get("status") or "unknown"
        collected_at = ev.get("collected_at") or ""
        notes = ev.get("notes") or ""

        lines.append(f"### {c.title_en}\n")
        lines.append(f"*{c.title_dk}*\n\n")
        lines.append(f"- Key: `{c.key}`\n")
        lines.append(f"- Provider: `{c.provider}`\n")
        lines.append(f"- Status: **{status}**\n")
        if c.iso27001_clauses:
            lines.append(f"- ISO 27001:2022: {', '.join(c.iso27001_clauses)}\n")
        if c.nis2_articles:
            lines.append(f"- NIS2: {', '.join(c.nis2_articles)}\n")
        if collected_at:
            lines.append(f"- Collected at (UTC): {collected_at}\n")
        if notes:
            lines.append("\n")
            lines.append(notes.strip() + "\n")
        lines.append("\n")

    # Manual attestation controls
    if attestation_controls:
        lines.append("## Manual Attestations\n\n")
        lines.append(
            "The following controls require human certification "
            "and cannot be collected automatically.\n\n"
        )
        for c in attestation_controls:
            ev = evidence_by_key.get(c.key) or {}
            status = ev.get("status") or "unknown"
            notes = ev.get("notes") or ""
            art = ev.get("artifacts") or {}
            attested_by = art.get("attested_by") or ""
            attested_at = art.get("attested_at") or ""

            lines.append(f"### {c.title_en}\n")
            lines.append(f"*{c.title_dk}*\n\n")
            if c.description_en:
                lines.append(f"{c.description_en}\n\n")
            lines.append(f"- Status: **{status}**\n")
            if c.iso27001_clauses:
                lines.append(f"- ISO 27001:2022: {', '.join(c.iso27001_clauses)}\n")
            if c.nis2_articles:
                lines.append(f"- NIS2: {', '.join(c.nis2_articles)}\n")
            if attested_by:
                lines.append(f"- Attested by: {attested_by}\n")
            if attested_at:
                lines.append(f"- Attested at: {str(attested_at)[:10]}\n")
            if notes:
                lines.append("\n")
                lines.append(notes.strip() + "\n")
            lines.append("\n")

    # Signature block
    lines.append("---\n\n")
    lines.append("## Signatur / Signature\n\n")
    lines.append(f"Dato / Date: {generated_at.strftime('%d-%m-%Y')}  \n")
    lines.append(f"Navn / Name: {officer_name or '________________________________'}  \n")
    lines.append(f"Titel / Title: {officer_title or '________________________________'}  \n")
    lines.append("Underskrift / Signature: ________________________________  \n\n")
    lines.append(
        "*Denne rapport er genereret automatisk og er vejledende. "
        "/ This report is automatically generated and indicative.*\n"
    )

    return "".join(lines)
