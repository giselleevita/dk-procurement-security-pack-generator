from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    engine_kwargs: dict[str, int | bool] = {"pool_pre_ping": True}
    if not settings.database_url.startswith("sqlite"):
        engine_kwargs.update(
            {
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
                "pool_timeout": settings.db_pool_timeout_sec,
                "pool_recycle": settings.db_pool_recycle_sec,
            }
        )
    return create_engine(settings.database_url, **engine_kwargs)


@lru_cache
def _sessionmaker():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    db = _sessionmaker()()
    try:
        yield db
    finally:
        db.close()

