from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repos.evidence import add_control_evidence, create_run, finish_run
from app.services.control_defs import CONTROL_BY_KEY


_HEADER_CANDIDATES = {
    "control": ("control_key", "control", "control_name", "name", "title", "requirement"),
    "status": ("status", "state", "result", "compliance_status"),
    "notes": ("notes", "comment", "comments", "description", "evidence"),
    "provider": ("provider", "source", "system"),
    "external_id": ("external_id", "id", "sys_id", "control_id"),
}

_SERVICENOW_CONTROL_MAP = {
    "security defaults": "ms.security_defaults",
    "conditional access": "ms.conditional_access_presence",
    "admin surface area": "ms.admin_surface_area",
    "branch protection": "gh.branch_protection",
    "pr reviews required": "gh.pr_reviews_required",
    "pull request reviews required": "gh.pr_reviews_required",
    "force pushes disabled": "gh.force_pushes_disabled",
    "enforce admins": "gh.enforce_admins",
    "repo visibility review": "gh.repo_visibility_review",
    "evidence freshness": "pack.evidence_freshness",
    "documentation completeness": "pack.documentation_completeness",
    "export integrity": "pack.export_integrity",
    "connection status": "pack.connection_status",
}


@dataclass(frozen=True)
class ImportedControlRow:
    row_number: int
    control_key: str
    status: str
    provider: str
    notes: str
    artifacts: dict


def _normalize_label(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def _pick_value(row: dict[str, str], kind: str) -> str:
    for key in _HEADER_CANDIDATES[kind]:
        raw = row.get(key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    return ""


def _resolve_control_key(raw_value: str) -> str | None:
    if not raw_value:
        return None
    stripped = raw_value.strip()
    if stripped in CONTROL_BY_KEY:
        return stripped
    normalized = _normalize_label(stripped)
    if normalized in _SERVICENOW_CONTROL_MAP:
        return _SERVICENOW_CONTROL_MAP[normalized]
    for control_key, control in CONTROL_BY_KEY.items():
        if normalized in {_normalize_label(control.title_en), _normalize_label(control.title_dk)}:
            return control_key
    return None


def _normalize_status(raw_value: str) -> str:
    normalized = _normalize_label(raw_value)
    if normalized in {"pass", "passing", "implemented", "compliant", "ok", "green"}:
        return "pass"
    if normalized in {"warn", "warning", "partial", "partially implemented", "in progress", "amber", "yellow"}:
        return "warn"
    if normalized in {"fail", "failed", "not implemented", "non compliant", "noncompliant", "red"}:
        return "fail"
    return "unknown"


def parse_grc_csv(csv_bytes: bytes) -> tuple[list[ImportedControlRow], list[str], int]:
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    warnings: list[str] = []
    imported: list[ImportedControlRow] = []

    if not reader.fieldnames:
        return [], ["CSV file is missing headers"], 0

    row_count = 0
    for index, raw_row in enumerate(reader, start=2):
        row_count += 1
        row = {str(key).strip().lower(): str(value or "").strip() for key, value in raw_row.items() if key is not None}
        raw_control = _pick_value(row, "control")
        control_key = _resolve_control_key(raw_control)
        if control_key is None:
            warnings.append(f"row {index}: unmapped control '{raw_control or 'missing'}'")
            continue
        raw_status = _pick_value(row, "status") or "unknown"
        status = _normalize_status(raw_status)
        provider = _pick_value(row, "provider") or "servicenow_grc"
        notes = _pick_value(row, "notes") or f"Imported from ServiceNow GRC row {index}"
        external_id = _pick_value(row, "external_id")
        imported.append(
            ImportedControlRow(
                row_number=index,
                control_key=control_key,
                status=status,
                provider=provider,
                notes=notes,
                artifacts={
                    "source_system": "servicenow_grc",
                    "raw_control": raw_control,
                    "raw_status": raw_status,
                    "external_id": external_id,
                    "row_number": index,
                },
            )
        )
    return imported, warnings, row_count


def import_grc_csv(db: Session, *, user_id, csv_bytes: bytes, dry_run: bool) -> dict:
    rows, warnings, row_count = parse_grc_csv(csv_bytes)

    response = {
        "source_system": "servicenow_grc",
        "dry_run": dry_run,
        "rows_total": row_count,
        "rows_mapped": len(rows),
        "rows_imported": 0,
        "warnings": warnings,
        "preview": [
            {
                "row_number": row.row_number,
                "control_key": row.control_key,
                "status": row.status,
                "provider": row.provider,
                "notes": row.notes,
            }
            for row in rows[:25]
        ],
    }

    if dry_run or not rows:
        return response

    run = create_run(db, user_id=user_id)
    for row in rows:
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run.id,
            control_key=row.control_key,
            provider=row.provider,
            status=row.status,
            artifacts=row.artifacts,
            notes=row.notes,
        )
    finish_run(db, run_id=run.id, status="success", error_summary=None)
    response["rows_imported"] = len(rows)
    response["import_run_id"] = str(run.id)
    return response