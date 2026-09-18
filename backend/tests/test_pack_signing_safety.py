from __future__ import annotations

import base64
import json

import pytest

from app.core.settings import get_settings
from app.services import pack_signing


def _configure(monkeypatch, tmp_path, key_byte: bytes = b"k") -> None:
    monkeypatch.setenv("FERNET_KEY", base64.urlsafe_b64encode(key_byte * 32).decode())
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    get_settings.cache_clear()
    monkeypatch.setattr(pack_signing, "_state_dir", lambda: tmp_path)


def test_first_use_creates_ed25519_material_with_restrictive_permissions(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    material = pack_signing.ensure_signing_material()

    assert material.mode == "ed25519"
    assert material.public_key_b64
    assert pack_signing._state_path().stat().st_mode & 0o077 == 0
    assert not list(tmp_path.glob("*.tmp"))


def test_corrupt_existing_state_fails_closed_without_replacement(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    path = pack_signing._state_path()
    path.write_text("not-json", encoding="utf-8")

    with pytest.raises(pack_signing.SigningMaterialUnavailable, match="explicit rotation"):
        pack_signing.ensure_signing_material()

    assert path.read_text(encoding="utf-8") == "not-json"


def test_undecryptable_existing_state_fails_closed(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path, b"a")
    pack_signing.ensure_signing_material()

    _configure(monkeypatch, tmp_path, b"b")
    with pytest.raises(pack_signing.SigningMaterialUnavailable, match="explicit rotation"):
        pack_signing.ensure_signing_material()


def test_explicit_rotation_changes_signer_and_preserves_public_record(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    previous = pack_signing.ensure_signing_material()

    current = pack_signing.rotate_signing_material()

    assert current.signer_id != previous.signer_id
    record_path = tmp_path / "signing-public-keys" / f"{previous.signer_id}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["public_key_b64"] == previous.public_key_b64
    assert record["signer_id"] == previous.signer_id
    assert "encrypted_private_key" not in record


def test_readiness_never_exposes_key_material(monkeypatch, tmp_path):
    _configure(monkeypatch, tmp_path)
    readiness = pack_signing.signing_readiness()

    assert readiness["ready"] is True
    assert readiness["mode"] == "ed25519"
    assert readiness["signer_id"]
    assert "public_key_b64" not in readiness
