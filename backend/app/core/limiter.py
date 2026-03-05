"""Central rate-limiter instance shared across all route modules.

Uses slowapi (Starlette-compatible) with in-memory storage (suitable for
single-instance deployments). Key function = remote IP address.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# default_limits applies to ALL routes via SlowAPIMiddleware.
# Per-route @limiter.limit() decorators are intentionally avoided because they
# interfere with FastAPI's dependency-injection signature inspection when
# Pydantic body models are present (causing spurious 422 responses).
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
