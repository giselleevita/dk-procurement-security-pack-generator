from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return an aware UTC timestamp.

    Use this instead of datetime.utcnow() to avoid tz-naive datetimes and
    upcoming stdlib deprecations.
    """

    return datetime.now(timezone.utc)


def isoformat_z(dt: datetime) -> str:
    """Serialize a datetime as ISO 8601 with a trailing 'Z' for UTC."""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    # Keep output stable as "...Z" (not "+00:00") to match existing exports.
    return dt.isoformat().replace("+00:00", "Z")
