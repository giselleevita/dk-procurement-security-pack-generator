from __future__ import annotations

import base64
import hashlib
import json
from io import BytesIO
from zipfile import ZipFile

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_ctx
from app.db.session import get_db
from app.services.export_store import load_export_pack
from app.services.pack_signing import canonical_manifest_bytes, ensure_signing_material

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/{export_id}/verify")
def verify_export(
    export_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_ctx),
) -> dict:
    # Export packs are stored per-user on this instance.
    pack_bytes = load_export_pack(user_id=str(auth.user.id), export_id=export_id)
    if pack_bytes is None:
        return {"verified": False, "mode": "unknown", "details": {"error": "not_found"}}

    details: dict = {"export_id": export_id}

    try:
        with ZipFile(BytesIO(pack_bytes), "r") as outer:
            pack_manifest_bytes = outer.read("pack_manifest.json")
            sig_text = outer.read("pack_manifest.sig").decode("utf-8").strip()
            sig_bytes = base64.b64decode(sig_text.encode("ascii"))

            manifest = json.loads(pack_manifest_bytes.decode("utf-8"))
            hashes = manifest.get("hashes") or {}

            missing = []
            mismatches = []
            for fn, expected in sorted(hashes.items()):
                try:
                    data = outer.read(fn)
                except KeyError:
                    missing.append(fn)
                    continue
                got = hashlib.sha256(data).hexdigest()
                if got != expected:
                    mismatches.append({"filename": fn, "expected": expected, "got": got})

            signing = ensure_signing_material()
            canonical = canonical_manifest_bytes(manifest)
            signature_ok = signing.verify(canonical, sig_bytes)

            details.update(
                {
                    "signature_valid": signature_ok,
                    "missing_files": missing,
                    "hash_mismatches": mismatches,
                }
            )

            verified = signature_ok and not missing and not mismatches
            return {"verified": verified, "mode": signing.mode, "details": details}
    except Exception as e:
        return {"verified": False, "mode": "unknown", "details": {"error": "verify_failed", "error_type": type(e).__name__}}
