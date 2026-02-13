import base64
import os
from io import BytesIO
from zipfile import ZipFile

import pytest


def _fernet_key() -> str:
    # urlsafe base64 of 32 bytes
    return base64.urlsafe_b64encode(b"0" * 32).decode("utf-8")


def test_fernet_roundtrip(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.crypto.fernet import decrypt_str, encrypt_str

    ct = encrypt_str("secret-token")
    assert ct != "secret-token"
    assert decrypt_str(ct) == "secret-token"


def test_evidence_zip_manifest_hashes():
    from datetime import datetime

    from app.export.evidence_zip import build_evidence_zip

    payload, manifest = build_evidence_zip(
        generated_at=datetime(2026, 1, 1),
        app_version="0.1.0",
        user_id="u1",
        evidence_by_key={
            "c1": {"status": "pass", "collected_at": "t", "notes": "n", "artifacts": {"a": 1}},
            "c2": {"status": "warn", "collected_at": "t2", "notes": "", "artifacts": {}},
        },
    )

    with ZipFile(BytesIO(payload), "r") as z:
        m = z.read("manifest.json")
        assert m
        for f in manifest["files"]:
            data = z.read(f["filename"])
            import hashlib

            assert hashlib.sha256(data).hexdigest() == f["sha256"]

