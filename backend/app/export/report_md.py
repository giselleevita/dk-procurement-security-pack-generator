from __future__ import annotations

from datetime import datetime

from app.services.control_defs import CONTROL_BY_KEY, CONTROLS


def render_report_md(*, generated_at: datetime, evidence_by_key: dict[str, dict]) -> str:
    lines: list[str] = []
    lines.append("# DK Procurement Security Pack\n")
    lines.append(f"Generated (UTC): {generated_at.isoformat()}Z\n")
    lines.append("\n")
    lines.append("## Controls\n")

    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        status = ev.get("status") or "unknown"
        collected_at = ev.get("collected_at") or ""
        notes = ev.get("notes") or ""

        lines.append(f"### {c.title_dk}\n")
        lines.append(f"### {c.title_en}\n")
        lines.append(f"- Key: `{c.key}`\n")
        lines.append(f"- Status: **{status}**\n")
        if collected_at:
            lines.append(f"- Collected at (UTC): {collected_at}\n")
        if notes:
            lines.append("\n")
            lines.append(notes.strip() + "\n")
        lines.append("\n")

    return "".join(lines)

