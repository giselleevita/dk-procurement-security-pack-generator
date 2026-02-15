from __future__ import annotations

import argparse

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_engine
from app.models.user import User
from app.repos.audit_events import delete_all_for_user as delete_audit
from app.repos.connections import delete_connection
from app.repos.evidence import delete_all_user_data
from app.repos.oauth_states import delete_all_for_user as delete_oauth_states
from app.repos.sessions import delete_all_sessions_for_user
from app.repos.users import get_user_by_email
from app.services.collect import write_demo_snapshot
from app.services.export_store import delete_exports_for_user


DEFAULT_DEMO_EMAIL = "demo@example.com"
DEFAULT_DEMO_PASSWORD = "password123"


def _ensure_demo_user(db: Session, *, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if user is None:
        user = User(email=email, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # Keep demo login predictable.
    user.password_hash = hash_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _wipe_user_but_keep_account(db: Session, *, user_id) -> None:
    delete_all_user_data(db, user_id=user_id)
    delete_oauth_states(db, user_id=user_id)
    delete_connection(db, user_id=user_id, provider="github")
    delete_connection(db, user_id=user_id, provider="microsoft")
    delete_all_sessions_for_user(db, user_id=user_id)
    delete_audit(db, user_id=user_id)
    delete_exports_for_user(user_id=str(user_id))


def main() -> int:
    p = argparse.ArgumentParser(description="Seed a deterministic demo user + evidence snapshot (local only).")
    p.add_argument("--email", default=DEFAULT_DEMO_EMAIL)
    p.add_argument("--password", default=DEFAULT_DEMO_PASSWORD)
    args = p.parse_args()

    engine = get_engine()
    with Session(engine) as db:
        user = _ensure_demo_user(db, email=args.email, password=args.password)
        _wipe_user_but_keep_account(db, user_id=user.id)
        res = write_demo_snapshot(db, user_id=user.id)
        print(f"Seeded demo for {user.email}: run_id={res['run_id']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
