from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.control_defs import CONTROLS

_STATUS_COLORS = {
    "pass": colors.HexColor("#d4edda"),
    "warn": colors.HexColor("#fff3cd"),
    "fail": colors.HexColor("#f8d7da"),
    "unknown": colors.HexColor("#f0f0f0"),
}


def render_report_pdf(
    *,
    generated_at: datetime,
    app_version: str,
    evidence_by_key: dict[str, dict],
    vendor: dict | None = None,
) -> bytes:
    vendor = vendor or {}

    company = vendor.get("company_name") or ""
    cvr = vendor.get("cvr_number") or ""
    address = vendor.get("address") or ""
    contact_name = vendor.get("contact_name") or ""
    contact_email = vendor.get("contact_email") or ""
    officer_name = vendor.get("security_officer_name") or ""
    officer_title = vendor.get("security_officer_title") or ""
    scope = vendor.get("pack_scope") or ""
    recipient = vendor.get("pack_recipient") or ""
    validity_months = vendor.get("pack_validity_months") or 6

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

    cover_title = ParagraphStyle(
        "cover_title", fontName="Helvetica-Bold", fontSize=22, leading=28, spaceAfter=6, alignment=1
    )
    cover_sub = ParagraphStyle(
        "cover_sub", fontName="Helvetica-Bold", fontSize=14, leading=18, spaceAfter=6, alignment=1
    )
    cover_meta = ParagraphStyle(
        "cover_meta", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=4, alignment=1
    )
    h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=12, leading=15, spaceAfter=6)
    h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10, leading=13, spaceAfter=3)
    p = ParagraphStyle("p", fontName="Helvetica", fontSize=10, leading=13, spaceAfter=8)
    muted = ParagraphStyle(
        "muted", fontName="Helvetica-Oblique", fontSize=9, leading=12, spaceAfter=4,
        textColor=colors.HexColor("#555555"),
    )

    # Deterministic evidence summary.
    status_counts = {"pass": 0, "warn": 0, "fail": 0, "unknown": 0}
    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        st = (ev.get("status") or "unknown").lower()
        status_counts[st] = status_counts.get(st, 0) + 1

    story = []

    # ── Cover Page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("DK Procurement Security Pack", cover_title))
    story.append(Spacer(1, 4 * mm))
    if company:
        story.append(Paragraph(company, cover_sub))
        if cvr:
            story.append(Paragraph(f"CVR: {cvr}", cover_meta))
        if address:
            story.append(Paragraph(address, cover_meta))
    story.append(Spacer(1, 8 * mm))
    if scope:
        story.append(Paragraph(f"Scope: {scope}", cover_meta))
    if recipient:
        story.append(Paragraph(f"Recipient: {recipient}", cover_meta))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"Generated: {generated_at.strftime('%d %B %Y')} UTC", cover_meta))
    story.append(Paragraph(f"Valid for: {validity_months} months", cover_meta))
    story.append(Paragraph(f"App version: {app_version}", cover_meta))
    story.append(Spacer(1, 16 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 6 * mm))
    summary_line = (
        f"Pass: {status_counts.get('pass', 0)}  ·  Warn: {status_counts.get('warn', 0)}  ·  "
        f"Fail: {status_counts.get('fail', 0)}  ·  Unknown: {status_counts.get('unknown', 0)}"
    )
    story.append(Paragraph(summary_line, cover_meta))
    story.append(PageBreak())

    # ── Data Handling ─────────────────────────────────────────────────────────
    story.append(Paragraph("Data Handling Statement (EN)", h))
    story.append(
        Paragraph(
            "Generated locally (self-hosted). No telemetry/external analytics. "
            "OAuth tokens stored encrypted (Fernet). "
            "Evidence fetched only on manual collect. Exports contain no tokens/secrets/keys. "
            "Delete via Forget provider / Wipe all data.",
            p,
        )
    )
    story.append(Paragraph("Databehandling (DK)", h))
    story.append(
        Paragraph(
            "Lokal generering (self-hosted). Ingen telemetry/ekstern analytics. "
            "OAuth tokens lagres krypteret (Fernet). "
            "Evidens hentes kun ved manuel collect. Eksporter indeholder ikke tokens/secrets/keys. "
            "Slet via Forget provider / Wipe all data.",
            p,
        )
    )
    story.append(Spacer(1, 10))

    # ── Evidence Summary ──────────────────────────────────────────────────────
    story.append(Paragraph("Evidence Summary", h))
    story.append(
        Paragraph(
            f"Controls: {len(CONTROLS)}. "
            f"Pass: {status_counts.get('pass', 0)}. "
            f"Warn: {status_counts.get('warn', 0)}. "
            f"Fail: {status_counts.get('fail', 0)}. "
            f"Unknown: {status_counts.get('unknown', 0)}.",
            p,
        )
    )
    story.append(Spacer(1, 10))

    # ── Compliance Framework Mapping Table ────────────────────────────────────
    story.append(Paragraph("Compliance Framework Mapping", h))

    tbl_header = [["Control", "Status", "ISO 27001:2022", "NIS2"]]
    tbl_rows = []
    for c in CONTROLS:
        ev = evidence_by_key.get(c.key) or {}
        status = ev.get("status") or "unknown"
        iso = "\n".join(c.iso27001_clauses) if c.iso27001_clauses else "—"
        nis2 = "\n".join(c.nis2_articles) if c.nis2_articles else "—"
        tbl_rows.append([c.title_en, status, iso, nis2])

    tbl_data = tbl_header + tbl_rows
    tbl = Table(tbl_data, colWidths=[72 * mm, 18 * mm, 50 * mm, 32 * mm])

    base_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343a40")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    status_style = []
    for i, row in enumerate(tbl_rows, start=1):
        bg = _STATUS_COLORS.get(row[1], colors.white)
        status_style.append(("BACKGROUND", (1, i), (1, i), bg))

    tbl.setStyle(TableStyle(base_style + status_style))
    story.append(tbl)
    story.append(Spacer(1, 14))

    # ── Controls Detail ───────────────────────────────────────────────────────
    story.append(Paragraph("Controls", h))

    automated = [c for c in CONTROLS if not c.is_attestation]
    attestation_controls = [c for c in CONTROLS if c.is_attestation]

    for c in automated:
        ev = evidence_by_key.get(c.key) or {}
        status = ev.get("status") or "unknown"
        collected_at = ev.get("collected_at") or ""
        notes = (ev.get("notes") or "").strip()

        story.append(Paragraph(c.title_en, h2))
        story.append(Paragraph(c.title_dk, muted))
        meta_parts = [f"Key: {c.key}", f"Provider: {c.provider}", f"Status: {status}"]
        if collected_at:
            meta_parts.append(f"Collected: {str(collected_at)[:10]}")
        if c.iso27001_clauses:
            meta_parts.append(f"ISO: {', '.join(c.iso27001_clauses)}")
        if c.nis2_articles:
            meta_parts.append(f"NIS2: {', '.join(c.nis2_articles)}")
        story.append(Paragraph("  ·  ".join(meta_parts), muted))
        if notes:
            story.append(Paragraph(notes.replace("\n", "<br/>").strip(), p))
        story.append(Spacer(1, 6))

    if attestation_controls:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Manual Attestations", h))
        story.append(
            Paragraph(
                "The following controls require human certification "
                "and cannot be collected automatically.",
                p,
            )
        )
        story.append(Spacer(1, 6))
        for c in attestation_controls:
            ev = evidence_by_key.get(c.key) or {}
            status = ev.get("status") or "unknown"
            notes = (ev.get("notes") or "").strip()
            art = ev.get("artifacts") or {}
            attested_by = art.get("attested_by") or ""
            attested_at = art.get("attested_at") or ""

            story.append(Paragraph(c.title_en, h2))
            story.append(Paragraph(c.title_dk, muted))
            meta_parts = [f"Status: {status}"]
            if c.iso27001_clauses:
                meta_parts.append(f"ISO: {', '.join(c.iso27001_clauses)}")
            if c.nis2_articles:
                meta_parts.append(f"NIS2: {', '.join(c.nis2_articles)}")
            if attested_by:
                meta_parts.append(f"Attested by: {attested_by}")
            if attested_at:
                meta_parts.append(f"Attested at: {str(attested_at)[:10]}")
            story.append(Paragraph("  ·  ".join(meta_parts), muted))
            if notes:
                story.append(Paragraph(notes.replace("\n", "<br/>").strip(), p))
            story.append(Spacer(1, 6))

    # ── Signature Block ───────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Signatur / Signature", h))
    story.append(Paragraph(f"Dato / Date: {generated_at.strftime('%d-%m-%Y')}", p))
    story.append(
        Paragraph(
            f"Navn / Name: {officer_name or '________________________________'}",
            p,
        )
    )
    story.append(
        Paragraph(
            f"Titel / Title: {officer_title or '________________________________'}",
            p,
        )
    )
    story.append(Paragraph("Underskrift / Signature: ________________________________", p))
    contact_parts = [x for x in [contact_name, contact_email] if x]
    if contact_parts:
        story.append(Paragraph(f"Kontakt / Contact: {', '.join(contact_parts)}", muted))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "This report is automatically generated and indicative. "
            "Always verify evidence and seek legal counsel where required. "
            "/ Denne rapport er automatisk genereret og vejledende.",
            muted,
        )
    )

    doc.build(story)
    return buf.getvalue()
