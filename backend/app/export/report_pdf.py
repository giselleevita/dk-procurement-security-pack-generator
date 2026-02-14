from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.services.control_defs import CONTROLS


def render_report_pdf(*, generated_at: datetime, app_version: str, evidence_by_key: dict[str, dict]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="DK Procurement Security Pack",
    )

    title = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=10)
    h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=12, leading=15, spaceAfter=6)
    p = ParagraphStyle("p", fontName="Helvetica", fontSize=10, leading=13, spaceAfter=8)

    # Deterministic evidence summary.
    status_counts = {"pass": 0, "warn": 0, "fail": 0, "unknown": 0}
    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        st = (ev.get("status") or "unknown").lower()
        status_counts[st] = status_counts.get(st, 0) + 1

    story = []
    story.append(Paragraph("DK Procurement Security Pack", title))
    story.append(Paragraph(f"Generated (UTC): {generated_at.isoformat()}Z", p))
    story.append(Paragraph(f"App version: {app_version}", p))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Databehandling (DK)", h))
    story.append(
        Paragraph(
            "Lokal generering (self-hosted). Ingen telemetry/ekstern analytics. OAuth tokens lagres krypteret (Fernet). "
            "Evidens hentes kun ved manuel collect. Eksporter indeholder ikke tokens/secrets/keys. "
            "Slet via Forget provider / Wipe all data.",
            p,
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("Data handling statement (EN)", h))
    story.append(
        Paragraph(
            "Generated locally (self-hosted). No telemetry/external analytics. OAuth tokens stored encrypted (Fernet). "
            "Evidence fetched only on manual collect. Exports contain no tokens/secrets/keys. "
            "Delete via Forget provider / Wipe all data.",
            p,
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Evidence Summary", h))
    story.append(
        Paragraph(
            f"Controls: {len(CONTROLS)}. Pass: {status_counts.get('pass', 0)}. Warn: {status_counts.get('warn', 0)}. "
            f"Fail: {status_counts.get('fail', 0)}. Unknown: {status_counts.get('unknown', 0)}.",
            p,
        )
    )
    story.append(Spacer(1, 10))

    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        status = ev.get("status") or "unknown"
        collected_at = ev.get("collected_at") or ""
        notes = (ev.get("notes") or "").strip()

        story.append(Paragraph(c.title_dk, h))
        story.append(Paragraph(c.title_en, h))
        story.append(Paragraph(f"Key: {c.key}", p))
        story.append(Paragraph(f"Provider: {c.provider}", p))
        story.append(Paragraph(f"Status: {status}", p))
        if collected_at:
            story.append(Paragraph(f"Collected at (UTC): {collected_at}", p))
        if notes:
            story.append(Paragraph(notes.replace("\n", "<br/>").strip(), p))
        story.append(Spacer(1, 10))

    doc.build(story)
    return buf.getvalue()
