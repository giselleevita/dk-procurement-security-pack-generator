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

