from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.services.control_defs import CONTROLS


def render_report_pdf(*, generated_at: datetime, evidence_by_key: dict[str, dict]) -> bytes:
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

    story = []
    story.append(Paragraph("DK Procurement Security Pack", title))
    story.append(Paragraph(f"Generated (UTC): {generated_at.isoformat()}Z", p))
    story.append(Spacer(1, 8))

    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        status = ev.get("status") or "unknown"
        collected_at = ev.get("collected_at") or ""
        notes = (ev.get("notes") or "").strip()

        story.append(Paragraph(c.title_dk, h))
        story.append(Paragraph(c.title_en, h))
        story.append(Paragraph(f"Key: {c.key}", p))
        story.append(Paragraph(f"Status: {status}", p))
        if collected_at:
            story.append(Paragraph(f"Collected at (UTC): {collected_at}", p))
        if notes:
            story.append(Paragraph(notes.replace("\n", "<br/>"), p))
        story.append(Spacer(1, 10))

    doc.build(story)
    return buf.getvalue()

