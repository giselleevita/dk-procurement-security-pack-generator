from __future__ import annotations

from pathlib import Path

import pytest

from app.services import export_store
from app.services.export_store import export_pack_path


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
    assert path.parts[-3:] == (
        "users",
        "123e4567-e89b-12d3-a456-426614174000",
        f"{'a' * 32}.zip",
    )
