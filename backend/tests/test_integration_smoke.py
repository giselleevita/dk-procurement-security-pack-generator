import base64
import io
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.repos.audit_events import count_for_user


def _fernet_key() -> str:
    return base64.urlsafe_b64encode(b"1" * 32).decode("utf-8")


def test_smoke_register_collect_dashboard(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    r = client.post("/api/auth/register", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200
    set_cookie = (r.headers.get("set-cookie") or "").lower()
    assert "dkpack_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "max-age=" in set_cookie

    csrf = client.cookies.get("dkpack_csrf")
    assert csrf

    c = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert c.status_code == 200

    import uuid
    user_id = uuid.UUID(r.json()["id"])
    db = TestingSessionLocal()
    try:
        assert count_for_user(db, user_id=user_id) >= 1
    finally:
        db.close()

    r2 = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert r2.status_code == 200

    import uuid

    user_id = uuid.UUID(r.json()["id"])
    db = TestingSessionLocal()
    try:
        assert count_for_user(db, user_id=user_id) >= 1
    finally:
        db.close()

    dash = client.get("/api/dashboard")
    assert dash.status_code == 200
    assert len(dash.json()) == 12


def test_settings_rejects_wildcard_allowed_origins(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")

    from app.core.settings import get_settings, parse_allowed_origins

    get_settings.cache_clear()
    settings = get_settings()

    with pytest.raises(ValueError):
        parse_allowed_origins(settings)


def test_rate_limit_enforced_on_api_routes(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    first = client.post("/api/auth/register", json={"email": "rate@example.com", "password": "password123"})
    second = client.post("/api/auth/register", json={"email": "rate2@example.com", "password": "password123"})

    assert first.status_code == 200
    assert "x-request-id" in first.headers
    assert second.status_code == 429
    assert "x-request-id" in second.headers


def test_framework_gap_report_endpoint(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    r = client.post("/api/auth/register", json={"email": "gap@example.com", "password": "password123"})
    assert r.status_code == 200

    report = client.get("/api/frameworks/gap-report")
    assert report.status_code == 200
    payload = report.json()
    assert payload["summary"]["total_controls"] == 12
    assert isinstance(payload["frameworks"], list)
    assert isinstance(payload["priority_gaps"], list)


def test_controls_aging_alerts_endpoint(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv("EVIDENCE_AGE_ALERT_DAYS", "0")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    r = client.post("/api/auth/register", json={"email": "age@example.com", "password": "password123"})
    assert r.status_code == 200

    csrf = client.cookies.get("dkpack_csrf")
    assert csrf
    c = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert c.status_code == 200

    alerts = client.get("/api/controls/aging-alerts")
    assert alerts.status_code == 200
    body = alerts.json()
    assert isinstance(body, list)
    assert len(body) > 0
    assert {"key", "age_days", "threshold_days"}.issubset(set(body[0].keys()))


def test_import_grc_dry_run_and_commit(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db
    from app.repos.evidence import latest_evidence_all_controls

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    r = client.post("/api/auth/register", json={"email": "import@example.com", "password": "password123"})
    assert r.status_code == 200
    csrf = client.cookies.get("dkpack_csrf")
    assert csrf

    csv_payload = (
        "control,status,notes,external_id\n"
        "Security Defaults,Implemented,Imported from GRC,CTRL-1\n"
        "Unknown Legacy Control,Partial,Needs follow-up,CTRL-2\n"
    )

    dry_run = client.post(
        "/api/import/grc",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("grc.csv", io.BytesIO(csv_payload.encode("utf-8")), "text/csv")},
        data={"dry_run": "true"},
    )
    assert dry_run.status_code == 200
    dry_body = dry_run.json()
    assert dry_body["dry_run"] is True
    assert dry_body["rows_total"] == 2
    assert dry_body["rows_mapped"] == 1
    assert dry_body["rows_imported"] == 0
    assert dry_body["warnings"]

    commit = client.post(
        "/api/import/grc",
        headers={"X-CSRF-Token": csrf},
        files={"file": ("grc.csv", io.BytesIO(csv_payload.encode("utf-8")), "text/csv")},
        data={"dry_run": "false"},
    )
    assert commit.status_code == 200
    body = commit.json()
    assert body["dry_run"] is False
    assert body["rows_imported"] == 1
    assert body["import_run_id"]

    user_id = uuid.UUID(r.json()["id"])
    db = TestingSessionLocal()
    try:
        rows = latest_evidence_all_controls(db, user_id=user_id)
    finally:
        db.close()

    assert any(row.control_key == "ms.security_defaults" for row in rows)


def test_oauth_denial_redirect_is_user_readable(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "x")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "y")
    monkeypatch.setenv("GITHUB_OAUTH_REDIRECT_URI", "http://localhost:8000/api/oauth/github/callback")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app, base_url="http://testserver")

    r = client.post("/api/auth/register", json={"email": "b@example.com", "password": "password123"})
    assert r.status_code == 200
    csrf = client.cookies.get("dkpack_csrf")
    assert csrf

    c = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert c.status_code == 200

    import uuid
    user_id = uuid.UUID(r.json()["id"])
    db = TestingSessionLocal()
    try:
        assert count_for_user(db, user_id=user_id) >= 1
    finally:
        db.close()

    start = client.post("/api/oauth/github/start", headers={"X-CSRF-Token": csrf})
    assert start.status_code == 200
    authorize_url = start.json()["authorize_url"]
    # Extract state from URL
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(urlparse(authorize_url).query)["state"][0]
    query = parse_qs(urlparse(authorize_url).query)
    assert query["code_challenge_method"] == ["S256"]
    assert len(query["code_challenge"][0]) == 43

    from sqlalchemy import select
    from app.crypto.fernet import decrypt_str
    from app.models.oauth_state import OAuthState

    db = TestingSessionLocal()
    try:
        stored = db.execute(select(OAuthState).where(OAuthState.state == state)).scalar_one()
        verifier = decrypt_str(stored.encrypted_code_verifier)
        import base64
        import hashlib

        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        assert query["code_challenge"] == [expected]
    finally:
        db.close()

    cb = client.get(
        f"/api/oauth/github/callback?state={state}&error=access_denied&error_description=Denied",
        follow_redirects=False,
    )
    assert cb.status_code in (302, 307)
    assert "/connections" in cb.headers.get("location", "")
    assert "status=error" in cb.headers.get("location", "")


def test_collect_writes_complete_snapshot_even_on_provider_error(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Force a GitHub failure at repo listing time.
    from app.providers import github_api

    def boom(self, *, per_page: int = 100):
        raise RuntimeError("boom")

    monkeypatch.setattr(github_api.GitHubApi, "list_repos", boom)

    client = TestClient(app)
    r = client.post("/api/auth/register", json={"email": "c@example.com", "password": "password123"})
    assert r.status_code == 200
    csrf = client.cookies.get("dkpack_csrf")
    assert csrf

    c = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert c.status_code == 200

    import uuid
    user_id = uuid.UUID(r.json()["id"])
    db = TestingSessionLocal()
    try:
        assert count_for_user(db, user_id=user_id) >= 1
    finally:
        db.close()

    # Insert a fake github connection so collector attempts GitHub and hits the monkeypatch.
    from app.crypto.fernet import encrypt_str
    from app.repos.connections import upsert_connection

    import uuid

    db = TestingSessionLocal()
    try:
        upsert_connection(
            db,
            user_id=uuid.UUID(r.json()["id"]),
            provider="github",
            encrypted_access_token=encrypt_str("fake"),
            encrypted_refresh_token=None,
            scopes="",
            token_type="Bearer",
            expires_at=None,
            provider_account_id=None,
        )
    finally:
        db.close()

    res = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert res.status_code == 200

    dash = client.get("/api/dashboard").json()
    assert len(dash) == 12

    # GitHub controls should exist in this run even though provider call failed.
    detail = client.get("/api/controls/gh.branch_protection").json()
    assert detail["status"] == "unknown"


def test_forget_provider_deletes_tokens_and_provider_evidence(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    r = client.post("/api/auth/register", json={"email": "d@example.com", "password": "password123"})
    assert r.status_code == 200
    csrf = client.cookies.get("dkpack_csrf")
    assert csrf

    import uuid
    from app.crypto.fernet import encrypt_str
    from app.repos.connections import upsert_connection
    from app.repos.evidence import add_control_evidence, create_run

    user_id = uuid.UUID(r.json()["id"])
    db = TestingSessionLocal()
    try:
        upsert_connection(
            db,
            user_id=user_id,
            provider="github",
            encrypted_access_token=encrypt_str("fake"),
            encrypted_refresh_token=None,
            scopes="",
            token_type="Bearer",
            expires_at=None,
            provider_account_id=None,
        )
        run = create_run(db, user_id=user_id)
        add_control_evidence(
            db,
            user_id=user_id,
            run_id=run.id,
            control_key="gh.branch_protection",
            provider="github",
            status="pass",
            artifacts={"x": 1},
            notes="n",
        )
    finally:
        db.close()

    resp = client.delete("/api/connections/github", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 200

    db = TestingSessionLocal()
    try:
        # Forget provider logs exactly one audit event in this test.
        assert count_for_user(db, user_id=user_id) == 1
    finally:
        db.close()

    # Evidence should be cleared for that provider.
    detail = client.get("/api/controls/gh.branch_protection").json()
    assert detail["status"] == "unknown"


def test_wipe_deletes_all_user_data_and_logs_out(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    r = client.post("/api/auth/register", json={"email": "e@example.com", "password": "password123"})
    assert r.status_code == 200
    csrf = client.cookies.get("dkpack_csrf")
    assert csrf

    c = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert c.status_code == 200

    import uuid
    user_id = uuid.UUID(r.json()["id"])
    db = TestingSessionLocal()
    try:
        assert count_for_user(db, user_id=user_id) >= 1
    finally:
        db.close()

    w = client.post("/api/wipe", headers={"X-CSRF-Token": csrf})
    assert w.status_code == 200

    db = TestingSessionLocal()
    try:
        assert count_for_user(db, user_id=user_id) == 0
    finally:
        db.close()

    # Session should no longer be valid.
    me = client.get("/api/me")
    assert me.status_code == 401


def test_export_pack_verify_endpoint_detects_tampering(tmp_path, monkeypatch):
    import json
    from io import BytesIO
    from zipfile import ZipFile

    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv("EXPORTS_DIR", str(tmp_path))

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.main import create_app
    from app.db.session import get_db

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.create_all(bind=engine)

    client = TestClient(app)
    r = client.post("/api/auth/register", json={"email": "xpack@example.com", "password": "password123"})
    assert r.status_code == 200

    csrf = client.cookies.get("dkpack_csrf")
    assert csrf

    # Ensure an evidence run exists so export is allowed.
    c = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert c.status_code == 200

    exp = client.post("/api/export", headers={"X-CSRF-Token": csrf})
    assert exp.status_code == 200

    outer_bytes = exp.content
    with ZipFile(BytesIO(outer_bytes), "r") as outer:
        names = set(outer.namelist())
        assert "pack_manifest.json" in names
        assert "pack_manifest.sig" in names
        manifest = json.loads(outer.read("pack_manifest.json").decode("utf-8"))
        assert manifest["runtime_sku"] in {"demo", "production"}
        assert manifest["attestation"]["support_sla"]["name"]
        export_id = manifest["export_id"]

    v = client.get(f"/api/exports/{export_id}/verify")
    assert v.status_code == 200
    assert v.json()["verified"] is True

    # A second authenticated tenant cannot address the first tenant's stored export,
    # even when the opaque export identifier is known.
    other = TestClient(app)
    other_registration = other.post(
        "/api/auth/register",
        json={"email": "other-tenant@example.com", "password": "password123"},
    )
    assert other_registration.status_code == 200
    cross_tenant = other.get(f"/api/exports/{export_id}/verify")
    assert cross_tenant.status_code == 200
    assert cross_tenant.json() == {
        "verified": False,
        "mode": "unknown",
        "details": {"error": "not_found"},
    }

    # Tamper with report.md on disk without updating hashes/signature.
    import uuid

    user_id = uuid.UUID(r.json()["id"])
    pack_path = tmp_path / "users" / str(user_id) / f"{export_id}.zip"
    assert pack_path.exists()

    with ZipFile(BytesIO(pack_path.read_bytes()), "r") as z:
        items = [(n, z.read(n)) for n in z.namelist()]

    tampered = BytesIO()
    with ZipFile(tampered, "w") as z2:
        for name, data in items:
            if name == "report.md":
                z2.writestr(name, data + b"\nTAMPERED\n")
            else:
                z2.writestr(name, data)

    pack_path.write_bytes(tampered.getvalue())

    v2 = client.get(f"/api/exports/{export_id}/verify")
    assert v2.status_code == 200
    body = v2.json()
    assert body["verified"] is False
    assert body["details"]["hash_mismatches"], "Expected hash mismatch after tampering"
