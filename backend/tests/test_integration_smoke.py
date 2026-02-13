import base64

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
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

    csrf = client.cookies.get("dkpack_csrf")
    assert csrf

    r2 = client.post("/api/collect", headers={"X-CSRF-Token": csrf})
    assert r2.status_code == 200

    dash = client.get("/api/dashboard")
    assert dash.status_code == 200
    assert len(dash.json()) == 12


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

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
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

    start = client.post("/api/oauth/github/start", headers={"X-CSRF-Token": csrf})
    assert start.status_code == 200
    authorize_url = start.json()["authorize_url"]
    # Extract state from URL
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(urlparse(authorize_url).query)["state"][0]

    cb = client.get(f"/api/oauth/github/callback?state={state}&error=access_denied&error_description=Denied")
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

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
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
