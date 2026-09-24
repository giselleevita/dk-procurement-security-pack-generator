from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from app.services import export_store
from app.services.export_store import export_pack_path, load_export_pack


@pytest.mark.parametrize(
    "user_id",
    ("", ".", "..", "../other-user", "user/other", "user\\other", "user\nother"),
)
def test_export_path_rejects_unsafe_user_ids(user_id: str) -> None:
    with pytest.raises(ValueError, match="Invalid user_id"):
        export_pack_path(user_id=user_id, export_id="a" * 32)


def test_export_path_accepts_uuid_shaped_user_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(export_store, "_exports_root", lambda: tmp_path)
    path = export_pack_path(
        user_id="123e4567-e89b-12d3-a456-426614174000",
        export_id="a" * 32,
    )
    storage_id = hashlib.sha256(
        uuid.UUID("123e4567-e89b-12d3-a456-426614174000").bytes
    ).hexdigest()
    assert path.parts[-3:] == (
        "users",
        storage_id,
        f"{'a' * 32}.zip",
    )


def test_export_path_rejects_symlink_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    storage_id = hashlib.sha256(uuid.UUID(user_id).bytes).hexdigest()
    users_root = tmp_path / "users"
    outside = tmp_path / "outside"
    users_root.mkdir()
    outside.mkdir()
    (users_root / storage_id).symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(export_store, "_exports_root", lambda: tmp_path)

    with pytest.raises(ValueError, match="storage root"):
        export_pack_path(user_id=user_id, export_id="a" * 32)


def test_load_rejects_symlinked_export_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    export_id = "a" * 32
    storage_id = hashlib.sha256(uuid.UUID(user_id).bytes).hexdigest()
    user_dir = tmp_path / "users" / storage_id
    user_dir.mkdir(parents=True)
    outside = tmp_path / "outside.zip"
    outside.write_bytes(b"not-an-export")
    (user_dir / f"{export_id}.zip").symlink_to(outside)
    monkeypatch.setattr(export_store, "_exports_root", lambda: tmp_path)

    assert load_export_pack(user_id=user_id, export_id=export_id) is None
