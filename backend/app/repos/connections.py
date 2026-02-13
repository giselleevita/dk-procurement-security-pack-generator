from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.provider_connection import ProviderConnection


def get_connection(db: Session, *, user_id: uuid.UUID, provider: str) -> ProviderConnection | None:
    stmt = select(ProviderConnection).where(
        ProviderConnection.user_id == user_id,
        ProviderConnection.provider == provider,
    )
    return db.execute(stmt).scalars().first()


def list_connections(db: Session, *, user_id: uuid.UUID) -> list[ProviderConnection]:
    stmt = select(ProviderConnection).where(ProviderConnection.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


def upsert_connection(
    db: Session,
    *,
    user_id: uuid.UUID,
    provider: str,
    encrypted_access_token: str,
    encrypted_refresh_token: str | None,
    scopes: str,
    token_type: str,
    expires_at: datetime | None,
    provider_account_id: str | None,
) -> ProviderConnection:
    existing = get_connection(db, user_id=user_id, provider=provider)
    if existing is None:
        row = ProviderConnection(
            user_id=user_id,
            provider=provider,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypted_refresh_token,
            scopes=scopes,
            token_type=token_type,
            expires_at=expires_at,
            provider_account_id=provider_account_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    stmt = (
        update(ProviderConnection)
        .where(ProviderConnection.id == existing.id)
        .values(
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypted_refresh_token,
            scopes=scopes,
            token_type=token_type,
            expires_at=expires_at,
            provider_account_id=provider_account_id,
            updated_at=datetime.utcnow(),
        )
        .returning(ProviderConnection)
    )
    row = db.execute(stmt).scalars().first()
    db.commit()
    assert row is not None
    return row


def delete_connection(db: Session, *, user_id: uuid.UUID, provider: str) -> None:
    stmt = delete(ProviderConnection).where(
        ProviderConnection.user_id == user_id,
        ProviderConnection.provider == provider,
    )
    db.execute(stmt)
    db.commit()

