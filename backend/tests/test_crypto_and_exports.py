import base64
import re
from io import BytesIO
from zipfile import ZipFile

from app.core.time import utcnow


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


_JWT_LIKE_RE = re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b")


def _assert_no_secrets_in_texts(texts: list[str]) -> None:
    blob = "\n".join(texts).lower()

    # Common markers we never want to see in exported *text* files.
    forbidden_substrings = [
        "access_token",
        "refresh_token",
        "client_secret",
        "bearer ",
        "authorization:",
        "code=",
    ]
    for s in forbidden_substrings:
        assert s not in blob, f"Found forbidden marker in export text: {s}"

    # JWT-like tokens (3 base64url-ish segments separated by dots).
    assert _JWT_LIKE_RE.search(blob) is None, "Found JWT-like token pattern in export text"


def _read_text_files_from_zip(z: ZipFile) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name in z.namelist():
        lower = name.lower()
        if lower.endswith(".pdf"):
            continue
        if not (lower.endswith(".md") or lower.endswith(".json") or lower.endswith(".txt") or lower.endswith(".sig")):
            continue
        data = z.read(name)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            # If it is not valid UTF-8, treat it as non-text and skip to avoid false positives.
            continue
        out.append((name, text))
    return out


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

    with ZipFile(BytesIO(payload), "r") as z:
        texts = [t for _name, t in _read_text_files_from_zip(z)]
    _assert_no_secrets_in_texts(texts)


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
            collected_at=utcnow(),
        )

        outer_bytes = export_pack(db, user_id=user_id)
    finally:
        db.close()

    with ZipFile(BytesIO(outer_bytes), "r") as outer:
        names = set(outer.namelist())
        assert "report.md" in names
        assert "report.pdf" in names
        assert "evidence-pack.zip" in names
        assert "pack_manifest.json" in names
        assert "pack_manifest.sig" in names

        evidence_zip_bytes = outer.read("evidence-pack.zip")
        outer_texts = [t for _name, t in _read_text_files_from_zip(outer)]

    with ZipFile(BytesIO(evidence_zip_bytes), "r") as inner:
        assert "manifest.json" in inner.namelist()
        # At least one control artifact must exist.
        assert any(n.startswith("artifacts/") and n.endswith(".json") for n in inner.namelist())
        inner_texts = [t for _name, t in _read_text_files_from_zip(inner)]

    _assert_no_secrets_in_texts(outer_texts + inner_texts)
