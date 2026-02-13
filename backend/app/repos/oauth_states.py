from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.oauth_state import OAuthState


def create_state(
    db: Session,
    *,
    user_id: uuid.UUID,
    provider: str,
    state: str,
    expires_at: datetime,
) -> OAuthState:
    row = OAuthState(user_id=user_id, provider=provider, state=state, expires_at=expires_at)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def consume_state(db: Session, *, user_id: uuid.UUID, provider: str, state: str) -> OAuthState | None:
    stmt = select(OAuthState).where(
        OAuthState.user_id == user_id,
        OAuthState.provider == provider,
        OAuthState.state == state,
    )
    row = db.execute(stmt).scalars().first()
    if row is None:
        return None
    if row.expires_at < datetime.utcnow():
        delete_state(db, state=state)
        return None
    delete_state(db, state=state)
    return row


def delete_state(db: Session, *, state: str) -> None:
    stmt = delete(OAuthState).where(OAuthState.state == state)
    db.execute(stmt)
    db.commit()


def delete_expired_states(db: Session) -> None:
    stmt = delete(OAuthState).where(OAuthState.expires_at < datetime.utcnow())
    db.execute(stmt)
    db.commit()


def delete_all_for_user(db: Session, *, user_id: uuid.UUID) -> None:
    stmt = delete(OAuthState).where(OAuthState.user_id == user_id)
    db.execute(stmt)
    db.commit()
