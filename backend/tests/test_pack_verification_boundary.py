from __future__ import annotations

import base64
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.services.pack_signing import canonical_manifest_bytes
from app.services.pack_verification import verify_pack_bytes


def _signed_pack(monkeypatch, tmp_path, *, hashes: dict[str, str] | None = None, extra: dict[str, bytes] | None = None) -> bytes:
    monkeypatch.setenv("FERNET_KEY", base64.urlsafe_b64encode(b"v" * 32).decode())
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    from app.core.settings import get_settings
    from app.services import pack_signing

    get_settings.cache_clear()
    monkeypatch.setattr(pack_signing, "_state_dir", lambda: tmp_path)
    signing = pack_signing.ensure_signing_material()

    payloads = {
        "report.md": b"report",
        "report.pdf": b"%PDF-demo",
        "evidence-pack.zip": b"evidence",
    }
    import hashlib

    manifest = {
        "schema_version": "pack/v1",
        "signer_id": "test-signer",
        "mode": "ed25519",
        "public_key_b64": signing.public_key_b64,
        "hashes": hashes if hashes is not None else {
            name: hashlib.sha256(value).hexdigest() for name, value in payloads.items()
        },
    }
    manifest_bytes = canonical_manifest_bytes(manifest)
    signature = base64.b64encode(signing.sign(manifest_bytes)) + b"\n"

    out = BytesIO()
    with ZipFile(out, "w", compression=ZIP_DEFLATED) as archive:
        for name, value in payloads.items():
            archive.writestr(name, value)
        archive.writestr("pack_manifest.json", manifest_bytes)
        archive.writestr("pack_manifest.sig", signature)
        for name, value in (extra or {}).items():
            archive.writestr(name, value)
    return out.getvalue()


def test_accepts_exact_signed_inventory(monkeypatch, tmp_path):
    assert verify_pack_bytes(_signed_pack(monkeypatch, tmp_path)).valid


def test_rejects_signed_manifest_with_incomplete_hash_inventory(monkeypatch, tmp_path):
    result = verify_pack_bytes(_signed_pack(monkeypatch, tmp_path, hashes={}))
    assert not result.valid
    assert "manifest hash inventory must exactly match pack payloads" in result.errors


def test_rejects_unexpected_archive_entry(monkeypatch, tmp_path):
    result = verify_pack_bytes(_signed_pack(monkeypatch, tmp_path, extra={"../escape.txt": b"no"}))
    assert not result.valid
    assert "pack contains an unsafe filename" in result.errors
