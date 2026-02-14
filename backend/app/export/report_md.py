from __future__ import annotations

from datetime import datetime

from app.services.control_defs import CONTROLS


def render_report_md(*, generated_at: datetime, app_version: str, evidence_by_key: dict[str, dict]) -> str:
    lines: list[str] = []
    lines.append("# DK Procurement Security Pack\n\n")
    lines.append(f"Generated (UTC): {generated_at.isoformat()}Z\n")
    lines.append(f"App version: {app_version}\n\n")

    lines.append("## Databehandling (DK)\n")
    lines.append("- Denne pakke er genereret lokalt i jeres miljø (self-hosted).\n")
    lines.append("- Ingen telemetry og ingen ekstern analytics.\n")
    lines.append("- OAuth tokens lagres krypteret i databasen (Fernet).\n")
    lines.append('- Evidens hentes kun ved manuel "Collect now".\n')
    lines.append("- Eksportpakker indeholder ikke tokens, client secrets eller nøgler.\n")
    lines.append('- Data kan slettes via "Forget provider" og "Wipe all data".\n\n')

    lines.append("## Data handling statement (EN)\n")
    lines.append("- This pack is generated locally in your environment (self-hosted).\n")
    lines.append("- No telemetry and no external analytics.\n")
    lines.append("- OAuth tokens are stored encrypted in the database (Fernet).\n")
    lines.append('- Evidence is fetched only when you manually click "Collect now".\n')
    lines.append("- Export packs do not include tokens, client secrets, or encryption keys.\n")
    lines.append('- Data can be deleted via "Forget provider" and "Wipe all data".\n\n')

    # Evidence summary (deterministic from stored evidence).
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

    lines.append("## Evidensoversigt / Evidence Summary\n\n")
    lines.append(f"- Controls total: {len(CONTROLS)}\n")
    lines.append(f"- Pass: {status_counts.get('pass', 0)}\n")
    lines.append(f"- Warn: {status_counts.get('warn', 0)}\n")
    lines.append(f"- Fail: {status_counts.get('fail', 0)}\n")
    lines.append(f"- Unknown: {status_counts.get('unknown', 0)}\n\n")

    lines.append("### By provider\n\n")
    lines.append("| Provider | Pass | Warn | Fail | Unknown |\n")
    lines.append("|---|---:|---:|---:|---:|\n")
    for provider in ("microsoft", "github", "pack"):
        p = by_provider.get(provider, {"pass": 0, "warn": 0, "fail": 0, "unknown": 0})
        lines.append(f"| {provider} | {p['pass']} | {p['warn']} | {p['fail']} | {p['unknown']} |\n")
    lines.append("\n")

    if unknown_controls:
        lines.append("### Unknown controls (why)\n\n")
        for key, notes in unknown_controls:
            if notes:
                lines.append(f"- `{key}`: {notes}\n")
            else:
                lines.append(f"- `{key}`\n")
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

    lines.append("## Controls\n\n")

    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        status = ev.get("status") or "unknown"
        collected_at = ev.get("collected_at") or ""
        notes = ev.get("notes") or ""

        lines.append(f"### {c.title_dk}\n")
        lines.append(f"### {c.title_en}\n")
        lines.append(f"- Key: `{c.key}`\n")
        lines.append(f"- Provider: `{c.provider}`\n")
        lines.append(f"- Status: **{status}**\n")
        if collected_at:
            lines.append(f"- Collected at (UTC): {collected_at}\n")
        if notes:
            lines.append("\n")
            lines.append(notes.strip() + "\n")
        lines.append("\n")

    return "".join(lines)
