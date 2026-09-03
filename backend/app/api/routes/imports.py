from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.db.session import get_db
from app.repos.audit_events import add_audit_event
from app.services.grc_import import import_grc_csv
from app.core.settings import get_settings

router = APIRouter(prefix="/import", tags=["import"])


class ImportPreviewRow(BaseModel):
    row_number: int
    control_key: str
    status: str
    provider: str
    notes: str


class GrcImportResponse(BaseModel):
    source_system: str
    dry_run: bool
    rows_total: int
    rows_mapped: int
    rows_imported: int
    warnings: list[str]
    preview: list[ImportPreviewRow]
    import_run_id: str | None = None


@router.post("/grc", response_model=GrcImportResponse)
def import_grc(
    file: UploadFile = File(...),
    dry_run: bool = Form(True),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> GrcImportResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Expected a CSV file upload")

    if file.content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel"}:
        raise HTTPException(status_code=415, detail="Unsupported upload media type")

    maximum = get_settings().max_upload_bytes
    payload = file.file.read(maximum + 1)
    if len(payload) > maximum:
        raise HTTPException(status_code=413, detail=f"CSV exceeds the {maximum}-byte limit")
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty")

    result = import_grc_csv(db, user_id=auth.user.id, csv_bytes=payload, dry_run=dry_run)
    add_audit_event(
        db,
        user_id=auth.user.id,
        action="import_grc",
        metadata={
            "dry_run": dry_run,
            "rows_mapped": result["rows_mapped"],
            "rows_imported": result["rows_imported"],
            "warnings": len(result["warnings"]),
        },
    )
    return GrcImportResponse(**result)
