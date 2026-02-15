from __future__ import annotations

import re
from pathlib import Path

from app.core.settings import get_settings


_EXPORT_ID_RE = re.compile(r"^[a-f0-9]{32}$")


def _backend_root() -> Path:
    # backend/
    return Path(__file__).resolve().parents[3]


def _exports_root() -> Path:
    settings = get_settings()
    p = Path(settings.exports_dir)
    if p.is_absolute():
        return p
    return _backend_root() / p


def export_pack_path(*, user_id: str, export_id: str) -> Path:
    if not _EXPORT_ID_RE.match(export_id):
        raise ValueError("Invalid export_id")
    # Per-user namespace avoids collisions and enables wipe-by-user.
    return _exports_root() / "users" / user_id / f"{export_id}.zip"


def store_export_pack(*, user_id: str, export_id: str, pack_bytes: bytes) -> Path:
    path = export_pack_path(user_id=user_id, export_id=export_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".zip.tmp")
    tmp.write_bytes(pack_bytes)
    tmp.replace(path)
    return path


def load_export_pack(*, user_id: str, export_id: str) -> bytes | None:
    path = export_pack_path(user_id=user_id, export_id=export_id)
    if not path.exists():
        return None
    return path.read_bytes()


def delete_exports_for_user(*, user_id: str) -> None:
    # Best-effort recursive delete.
    root = _exports_root() / "users" / user_id
    if not root.exists():
        return
    for p in sorted(root.rglob("*"), reverse=True):
        try:
            if p.is_file() or p.is_symlink():
                p.unlink()
            elif p.is_dir():
                p.rmdir()
        except Exception:
            continue
    try:
        root.rmdir()
    except Exception:
        pass
