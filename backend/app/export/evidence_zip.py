from __future__ import annotations

import hashlib
import json
from datetime import datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile


def build_evidence_zip(*, generated_at: datetime, app_version: str, user_id: str, evidence_by_key: dict[str, dict]) -> tuple[bytes, dict]:
    """
    Returns (zip_bytes, manifest_dict).
    """
    files: list[dict] = []
    artifact_payloads: dict[str, bytes] = {}

    for key, ev in evidence_by_key.items():
        payload = json.dumps(
            {
                "control_key": key,
                "status": ev.get("status"),
                "collected_at": ev.get("collected_at"),
                "notes": ev.get("notes"),
                "artifacts": ev.get("artifacts") or {},
            },
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        sha = hashlib.sha256(payload).hexdigest()
        filename = f"artifacts/{key}.json"
        artifact_payloads[filename] = payload
        files.append({"control_key": key, "filename": filename, "sha256": sha})

    manifest = {
        "generated_at_utc": generated_at.isoformat() + "Z",
        "app_version": app_version,
        "user_id": user_id,
        "files": files,
    }

    buf = BytesIO()
    with ZipFile(buf, "w", compression=ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))
        for fn, payload in artifact_payloads.items():
            z.writestr(fn, payload)

    return buf.getvalue(), manifest
