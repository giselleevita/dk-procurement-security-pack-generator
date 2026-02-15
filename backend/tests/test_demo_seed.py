import base64


def _fernet_key() -> str:
    return base64.urlsafe_b64encode(b"2" * 32).decode("utf-8")


def test_demo_seed_writes_complete_snapshot(monkeypatch):
    import uuid

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("FERNET_KEY", _fernet_key())

    from app.core.settings import get_settings

    get_settings.cache_clear()

    from app.db.base import Base
    from app.models.user import User
    from app.repos.evidence import latest_evidence_all_controls
    from app.services.collect import write_demo_snapshot

    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    user_id = uuid.uuid4()
    with SessionLocal() as db:
        db.add(User(id=user_id, email="demo@example.com", password_hash="x"))
        db.commit()

        write_demo_snapshot(db, user_id=user_id)
        rows = latest_evidence_all_controls(db, user_id=user_id)

    assert len(rows) == 12
    assert set(r.control_key for r in rows) == {
        "ms.security_defaults",
        "ms.conditional_access_presence",
        "ms.admin_surface_area",
        "gh.branch_protection",
        "gh.pr_reviews_required",
        "gh.force_pushes_disabled",
        "gh.enforce_admins",
        "gh.repo_visibility_review",
        "pack.evidence_freshness",
        "pack.documentation_completeness",
        "pack.export_integrity",
        "pack.connection_status",
    }
