import base64
from io import BytesIO
from zipfile import ZipFile


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


def test_evidence_zip_contains_no_secrets_markers():
    from datetime import datetime

    from app.export.evidence_zip import build_evidence_zip

    payload, _manifest = build_evidence_zip(
        generated_at=datetime(2026, 1, 1),
        app_version="0.1.0",
        user_id="u1",
        evidence_by_key={
            "c1": {"status": "pass", "collected_at": "t", "notes": "n", "artifacts": {"repo": "a/b"}},
        },
    )

    # Read only the included files (avoid false positives by scanning raw compressed bytes).
    with ZipFile(BytesIO(payload), "r") as z:
        manifest = z.read("manifest.json").decode("utf-8").lower()
        artifact = z.read("artifacts/c1.json").decode("utf-8").lower()
        blob = (manifest + artifact).encode("utf-8")

    # Markers we never want to see in exports (tokens/secrets/callback codes).
    assert b"access_token" not in blob
    assert b"refresh_token" not in blob
    assert b"client_secret" not in blob
    assert b"bearer " not in blob
    assert b"code=" not in blob


def test_export_pack_contains_expected_files_and_no_secret_markers(monkeypatch):
    import uuid
    from datetime import datetime
    from io import BytesIO
    from zipfile import ZipFile

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.models.user import User
    from app.repos.evidence import add_control_evidence, create_run
    from app.services.export_pack import export_pack

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    user_id = uuid.uuid4()
    db = SessionLocal()
    try:
        db.add(User(id=user_id, email="z@example.com", password_hash="x"))
        db.commit()

        run = create_run(db, user_id=user_id)
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run.id,
            control_key="gh.branch_protection",
            provider="github",
            status="pass",
            artifacts={"repos_sampled": 1},
            notes="ok",
            collected_at=datetime.utcnow(),
        )

        outer_bytes = export_pack(db, user_id=user_id)
    finally:
        db.close()

    with ZipFile(BytesIO(outer_bytes), "r") as outer:
        names = set(outer.namelist())
        assert "report.md" in names
        assert "report.pdf" in names
        assert "evidence-pack.zip" in names

        report_md = outer.read("report.md").decode("utf-8").lower()
        evidence_zip_bytes = outer.read("evidence-pack.zip")

    with ZipFile(BytesIO(evidence_zip_bytes), "r") as inner:
        assert "manifest.json" in inner.namelist()
        # At least one control artifact must exist.
        assert any(n.startswith("artifacts/") and n.endswith(".json") for n in inner.namelist())
        manifest = inner.read("manifest.json").decode("utf-8").lower()

    blob = (report_md + manifest).encode("utf-8")
    assert b"access_token" not in blob
    assert b"refresh_token" not in blob
    assert b"client_secret" not in blob
    assert b"bearer " not in blob
    assert b"code=" not in blob
