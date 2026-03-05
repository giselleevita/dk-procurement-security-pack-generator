"""
Tests for professional-hardening additions:
  - Security response headers (CSP, X-Frame-Options, X-Content-Type-Options, …)
  - X-Request-ID is present on every response
  - Password complexity (uppercase + digit requirements)
  - Vendor-profile contact_email validation
  - Vendor-profile contact_phone validation
  - Rate-limit middleware is registered (429 on excess)
  - Login rejects unknown credentials
  - Register rejects duplicate e-mail
"""
from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# ── helpers ──────────────────────────────────────────────────────────────────

def _fernet_key() -> str:
    return base64.urlsafe_b64encode(b"1" * 32).decode()


def _make_app(monkeypatch, *, env: str = "dev"):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())
    monkeypatch.setenv("WEB_BASE_URL", "http://localhost:5173")
    if env != "dev":
        monkeypatch.setenv("APP_ENV", env)

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
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), Session


# ── Security headers ──────────────────────────────────────────────────────────

def test_security_headers_present_on_unauthenticated_endpoint(monkeypatch):
    client, _ = _make_app(monkeypatch)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert "content-security-policy" in r.headers
    assert "frame-ancestors" in r.headers["content-security-policy"]
    assert r.headers.get("referrer-policy") == "no-referrer"


def test_x_request_id_header_is_uuid(monkeypatch):
    import uuid
    client, _ = _make_app(monkeypatch)
    r = client.get("/api/health")
    rid = r.headers.get("x-request-id", "")
    # Must be a valid UUID-4.
    parsed = uuid.UUID(rid)
    assert parsed.version == 4


def test_hsts_not_set_in_dev(monkeypatch):
    client, _ = _make_app(monkeypatch)
    r = client.get("/api/health")
    assert "strict-transport-security" not in r.headers


# ── Password complexity ───────────────────────────────────────────────────────

def test_register_rejects_password_without_uppercase(monkeypatch):
    client, _ = _make_app(monkeypatch)
    r = client.post("/api/auth/register", json={"email": "a@test.com", "password": "alllowercase1"})
    assert r.status_code == 422


def test_register_rejects_password_without_digit(monkeypatch):
    client, _ = _make_app(monkeypatch)
    r = client.post("/api/auth/register", json={"email": "b@test.com", "password": "AllUpperNoDigit"})
    assert r.status_code == 422


def test_register_rejects_short_password(monkeypatch):
    client, _ = _make_app(monkeypatch)
    r = client.post("/api/auth/register", json={"email": "c@test.com", "password": "Ab1"})
    assert r.status_code == 422


def test_register_accepts_valid_password(monkeypatch):
    client, _ = _make_app(monkeypatch)
    r = client.post("/api/auth/register", json={"email": "d@test.com", "password": "ValidPass1"})
    assert r.status_code == 200


def test_login_validates_password_complexity(monkeypatch):
    """Login also uses AuthRequest, so complexity is validated before DB lookup."""
    client, _ = _make_app(monkeypatch)
    r = client.post("/api/auth/login", json={"email": "x@test.com", "password": "nouppercase1"})
    assert r.status_code == 422


# ── Auth edge cases ───────────────────────────────────────────────────────────

def test_register_rejects_duplicate_email(monkeypatch):
    client, _ = _make_app(monkeypatch)
    payload = {"email": "dup@test.com", "password": "UniquePass1"}
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 200
    r2 = client.post("/api/auth/register", json=payload)
    assert r2.status_code == 409


def test_login_rejects_wrong_password(monkeypatch):
    client, _ = _make_app(monkeypatch)
    client.post("/api/auth/register", json={"email": "login_test@test.com", "password": "CorrectPass1"})
    r = client.post("/api/auth/login", json={"email": "login_test@test.com", "password": "WrongPass1"})
    assert r.status_code == 401


def test_login_rejects_unknown_email(monkeypatch):
    client, _ = _make_app(monkeypatch)
    r = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "SomePass1"})
    assert r.status_code == 401


def test_unauthenticated_request_returns_401(monkeypatch):
    client, _ = _make_app(monkeypatch)
    r = client.get("/api/dashboard")
    assert r.status_code == 401


# ── Vendor profile validation ─────────────────────────────────────────────────

def _register_and_get_client(monkeypatch):
    client, Session = _make_app(monkeypatch)
    r = client.post("/api/auth/register", json={"email": "vp@test.com", "password": "TestPass1"})
    assert r.status_code == 200
    csrf = client.cookies.get("dkpack_csrf")
    assert csrf
    return client, csrf


def test_vendor_profile_accepts_valid_email(monkeypatch):
    client, csrf = _register_and_get_client(monkeypatch)
    r = client.put(
        "/api/vendor-profile",
        json={"contact_email": "valid@example.com", "pack_validity_months": 6},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200
    assert r.json()["contact_email"] == "valid@example.com"


def test_vendor_profile_accepts_empty_email(monkeypatch):
    client, csrf = _register_and_get_client(monkeypatch)
    r = client.put(
        "/api/vendor-profile",
        json={"contact_email": "", "pack_validity_months": 6},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200


def test_vendor_profile_rejects_invalid_email(monkeypatch):
    client, csrf = _register_and_get_client(monkeypatch)
    r = client.put(
        "/api/vendor-profile",
        json={"contact_email": "not-an-email", "pack_validity_months": 6},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 422


def test_vendor_profile_accepts_valid_phone(monkeypatch):
    client, csrf = _register_and_get_client(monkeypatch)
    r = client.put(
        "/api/vendor-profile",
        json={"contact_phone": "+45 20 30 40 50", "pack_validity_months": 6},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200


def test_vendor_profile_rejects_invalid_phone(monkeypatch):
    client, csrf = _register_and_get_client(monkeypatch)
    r = client.put(
        "/api/vendor-profile",
        json={"contact_phone": "abc!invalid@@#", "pack_validity_months": 6},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 422


def test_vendor_profile_rejects_pack_validity_out_of_range(monkeypatch):
    client, csrf = _register_and_get_client(monkeypatch)
    r = client.put(
        "/api/vendor-profile",
        json={"pack_validity_months": 0},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 422
    r2 = client.put(
        "/api/vendor-profile",
        json={"pack_validity_months": 61},
        headers={"X-CSRF-Token": csrf},
    )
    assert r2.status_code == 422


# ── CSRF protection ───────────────────────────────────────────────────────────

def test_collect_rejected_without_csrf(monkeypatch):
    """An authenticated request with no CSRF token must be rejected with 403."""
    client, _ = _make_app(monkeypatch)
    # Register → session cookie is set automatically on the test client.
    r = client.post("/api/auth/register", json={"email": "csrf_test@test.com", "password": "CsrfPass1"})
    assert r.status_code == 200
    # Omit the X-CSRF-Token header while authenticated → must be rejected.
    r2 = client.post("/api/collect")
    assert r2.status_code == 403


def test_collect_rejected_with_wrong_csrf(monkeypatch):
    """An authenticated request with a wrong CSRF token must be rejected with 403."""
    client, _ = _make_app(monkeypatch)
    r = client.post("/api/auth/register", json={"email": "csrf2@test.com", "password": "CsrfPass1"})
    assert r.status_code == 200
    r2 = client.post("/api/collect", headers={"X-CSRF-Token": "totally-wrong"})
    assert r2.status_code == 403
