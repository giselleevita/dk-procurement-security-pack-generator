from __future__ import annotations

import json
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx, require_csrf
from app.core.settings import get_settings
from app.db.session import get_db
from app.services.export_pack import export_pack
from app.services.pack_verification import verify_pack_bytes

router = APIRouter(prefix="/demo", tags=["demo"])


def _tamper_report(pack: bytes) -> bytes:
    source = BytesIO(pack)
    output = BytesIO()
    with ZipFile(source, "r") as original, ZipFile(output, "w", compression=ZIP_DEFLATED) as changed:
        for entry in original.infolist():
            payload = original.read(entry.filename)
            if entry.filename == "report.md":
                payload += b"\nUNSIGNED CHANGE\n"
            changed.writestr(entry.filename, payload)
    return output.getvalue()


@router.post("/golden-path")
def golden_path(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
    _: None = Depends(require_csrf),
) -> dict:
    """Run the complete synthetic export and independent-verification story."""
    if get_settings().app_env.lower() != "demo":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo mode is disabled")

    pack = export_pack(db, user_id=auth.user.id)
    original = verify_pack_bytes(pack)
    tampered = verify_pack_bytes(_tamper_report(pack))
    with ZipFile(BytesIO(pack), "r") as archive:
        manifest = json.loads(archive.read("pack_manifest.json"))

    return {
        "scenario": "synthetic-procurement-review",
        "steps": ["collect", "sign", "verify", "tamper-test"],
        "export_id": manifest["export_id"],
        "signer_id": original.signer_id,
        "schema_version": original.schema_version,
        "original_valid": original.valid,
        "tampered_valid": tampered.valid,
        "tamper_errors": tampered.errors,
        "artifact_hashes": manifest["hashes"],
    }
