from __future__ import annotations

import hashlib
from datetime import datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy.orm import Session

from app.export.evidence_zip import build_evidence_zip
from app.export.report_md import render_report_md
from app.export.report_pdf import render_report_pdf
from app.repos.evidence import add_control_evidence, latest_evidence_all_controls, latest_run
from app.services.control_defs import CONTROLS


def export_pack(db: Session, *, user_id) -> bytes:
    run = latest_run(db, user_id=user_id)
    if run is None:
        raise ValueError("No evidence collected yet")

    generated_at = datetime.utcnow()
    rows = {r.control_key: r for r in latest_evidence_all_controls(db, user_id=user_id)}
    evidence_by_key: dict[str, dict] = {}

    for c in CONTROLS:
        r = rows.get(c.key)
        if r is None:
            evidence_by_key[c.key] = {"status": "unknown", "collected_at": None, "notes": "No evidence.", "artifacts": {}}
            continue
        evidence_by_key[c.key] = {
            "status": r.status,
            "collected_at": r.collected_at.isoformat() + "Z",
            "notes": r.notes,
            "artifacts": r.artifacts,
        }

    report_md = render_report_md(generated_at=generated_at, evidence_by_key=evidence_by_key).encode("utf-8")
    report_pdf = render_report_pdf(generated_at=generated_at, evidence_by_key=evidence_by_key)

    evidence_zip_bytes, manifest = build_evidence_zip(
        generated_at=generated_at,
        app_version="0.1.0",
        user_id=str(user_id),
        evidence_by_key=evidence_by_key,
    )

    integrity_status, integrity_artifacts, integrity_notes = _validate_manifest(evidence_zip_bytes)
    add_control_evidence(
        db,
        user_id=user_id,
        run_id=run.id,
        control_key="pack.export_integrity",
        provider="pack",
        status=integrity_status,
        artifacts=integrity_artifacts,
        notes=integrity_notes,
        collected_at=generated_at,
    )

    outer = BytesIO()
    with ZipFile(outer, "w", compression=ZIP_DEFLATED) as z:
        z.writestr("report.md", report_md)
        z.writestr("report.pdf", report_pdf)
        z.writestr("evidence-pack.zip", evidence_zip_bytes)
    return outer.getvalue()


def _validate_manifest(evidence_zip_bytes: bytes) -> tuple[str, dict, str]:
    import json
    from zipfile import ZipFile

    try:
        with ZipFile(BytesIO(evidence_zip_bytes), "r") as z:
            manifest = json.loads(z.read("manifest.json").decode("utf-8"))
            files = manifest.get("files") or []
            missing = []
            bad_hash = []
            for f in files:
                fn = f.get("filename")
                expected = f.get("sha256")
                if not fn or not expected:
                    continue
                try:
                    payload = z.read(fn)
                except KeyError:
                    missing.append(fn)
                    continue
                got = hashlib.sha256(payload).hexdigest()
                if got != expected:
                    bad_hash.append({"filename": fn, "expected": expected, "got": got})

            status = "pass" if not missing and not bad_hash else "warn"
            artifacts = {"missing_files": missing, "bad_hashes": bad_hash}
            notes = "Export manifest validated." if status == "pass" else "Export manifest issues detected."
            return status, artifacts, notes
    except Exception as e:
        return "warn", {"error": str(e)}, "Unable to validate export manifest."

