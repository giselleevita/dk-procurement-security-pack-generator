from __future__ import annotations

import hashlib
import os
import re
import uuid
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


def _safe_export_id(export_id: str) -> str:
    safe_export_id = os.path.basename(export_id)
    if safe_export_id != export_id or not _EXPORT_ID_RE.fullmatch(safe_export_id):
        raise ValueError("Invalid export_id")
    return safe_export_id


def _user_storage_id(user_id: str) -> str:
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError) as exc:
        raise ValueError("Invalid user_id") from exc
    return hashlib.sha256(user_uuid.bytes).hexdigest()


def _users_root() -> Path:
    return (_exports_root() / "users").resolve(strict=False)


def _existing_user_exports_dir(*, user_id: str) -> Path | None:
    storage_id = _user_storage_id(user_id)
    users_root = _users_root()
    if not users_root.is_dir():
        return None
    for entry in users_root.iterdir():
        if entry.name != storage_id or entry.is_symlink() or not entry.is_dir():
            continue
        resolved = entry.resolve(strict=True)
        try:
            resolved.relative_to(users_root)
        except ValueError:
            return None
        return resolved
    return None


def export_pack_path(*, user_id: str, export_id: str) -> Path:
    safe_export_id = _safe_export_id(export_id)
    # Do not place request-derived account identifiers in filesystem segments.
    user_storage_id = _user_storage_id(user_id)
    users_root = _users_root()
    path = (users_root / user_storage_id / f"{safe_export_id}.zip").resolve(strict=False)
    try:
        path.relative_to(users_root)
    except ValueError as exc:
        raise ValueError("Export path escapes the configured storage root") from exc
    # Per-user namespace avoids collisions and enables wipe-by-user.
    return path


def store_export_pack(*, user_id: str, export_id: str, pack_bytes: bytes) -> Path:
    path = export_pack_path(user_id=user_id, export_id=export_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".zip.tmp")
    tmp.write_bytes(pack_bytes)
    tmp.replace(path)
    return path


def load_export_pack(*, user_id: str, export_id: str) -> bytes | None:
    safe_export_id = _safe_export_id(export_id)
    user_dir = _existing_user_exports_dir(user_id=user_id)
    if user_dir is None:
        return None
    expected_name = f"{safe_export_id}.zip"
    for entry in user_dir.iterdir():
        if entry.name != expected_name or entry.is_symlink() or not entry.is_file():
            continue
        resolved = entry.resolve(strict=True)
        try:
            resolved.relative_to(user_dir)
        except ValueError:
            return None
        return resolved.read_bytes()
    return None


def delete_exports_for_user(*, user_id: str) -> None:
    # Best-effort recursive delete.
    root = _existing_user_exports_dir(user_id=user_id)
    if root is None:
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
