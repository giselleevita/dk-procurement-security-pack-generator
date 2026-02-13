from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.session import Session as DbSession


def create_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    csrf_token: str,
    expires_at: datetime,
) -> DbSession:
    s = DbSession(
        user_id=user_id,
        token_hash=token_hash,
        csrf_token=csrf_token,
        expires_at=expires_at,
        last_seen_at=datetime.utcnow(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def get_session_by_token_hash(db: Session, token_hash: str) -> DbSession | None:
    stmt = select(DbSession).where(DbSession.token_hash == token_hash)
    return db.execute(stmt).scalars().first()


def touch_session(db: Session, session_id: uuid.UUID) -> None:
    stmt = update(DbSession).where(DbSession.id == session_id).values(last_seen_at=datetime.utcnow())
    db.execute(stmt)
    db.commit()


def revoke_session(db: Session, session_id: uuid.UUID) -> None:
    stmt = update(DbSession).where(DbSession.id == session_id).values(revoked_at=datetime.utcnow())
    db.execute(stmt)
    db.commit()

